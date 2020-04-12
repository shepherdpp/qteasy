# coding=utf-8

import pandas as pd
import tushare as ts
import numpy as np
from datetime import datetime
import datetime as dt

TUSHARE_TOKEN = '14f96621db7a937c954b1943a579f52c09bbd5022ed3f03510b77369'
ts.set_token(TUSHARE_TOKEN)

PRICE_TYPE_DATA = ['close',
                   'open',
                   'high',
                   'low',
                   'pre_close',
                   'change',
                   'pct_chg',
                   'vol',
                   'amount']
FINANCIAL_REPORT_TYPE_DATA = ['basic_eps',
                              'diluted_eps',
                              'total_revenue',
                              'revenue',
                              'int_income',
                              'prem_earned',
                              'comm_income',
                              'n_commis_income',
                              'n_oth_income',
                              'n_oth_b_income',
                              'prem_income',
                              'out_prem',
                              'une_prem_reser',
                              'reins_income',
                              'n_sec_tb_income',
                              'n_sec_uw_income',
                              'n_asset_mg_income',
                              'oth_b_income',
                              'fv_value_chg_gain',
                              'invest_income',
                              'ass_invest_income',
                              'forex_gain',
                              'total_cogs',
                              'oper_cost',
                              'int_exp',
                              'comm_exp',
                              'biz_tax_surchg',
                              'sell_exp',
                              'admin_exp',
                              'fin_exp',
                              'assets_impair_loss',
                              'prem_refund',
                              'compens_payout',
                              'reser_insur_liab',
                              'div_payt',
                              'reins_exp',
                              'oper_exp',
                              'compens_payout_refu',
                              'insur_reser_refu',
                              'reins_cost_refund',
                              'other_bus_cost',
                              'operate_profit',
                              'non_oper_income',
                              'non_oper_exp',
                              'nca_disploss',
                              'total_profit',
                              'income_tax',
                              'n_income',
                              'n_income_attr_p',
                              'minority_gain',
                              'oth_compr_income',
                              't_compr_income',
                              'compr_inc_attr_p',
                              'compr_inc_attr_m_s',
                              'ebit',
                              'ebitda',
                              'insurance_exp',
                              'undist_profit',
                              'distable_profit']
COMPOSIT_TYPE_DATA = []

# TODO: 将History类重新定义为History模块，取消类的定义，转而使History模块变成对历史数据进行操作或读取的一个函数包的集合


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
            HistoryPanel.rows 输出一个字典，包含所有日期行标签及其对应的行号，从0开始知道N-1）
        3, 方便地打印HistoryPanel的相关信息
        4, 方便地打印及格式化输出HistoryPanel的内容
        5, 方便地与pandas DataFrame对象互相转化
            HistoryPanel不能完整转化为DataFrame对象，因为DataFrame只能适应2D数据。在转化为DataFrame的时候，用户只能选择
            HistoryPanel的一个切片，或者是一个股票品种，或者是一个数据类型，输出的DataFrame包含的数据行数与
        6, 方便地由多个pandas DataFrame对象组合而成
    """

    # TODO 应该把rows的格式转化为pandas.Timestamp()对象
    def __init__(self, values:np.ndarray = None, levels=None, rows=None, columns=None):
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
            assert isinstance(values, np.ndarray), f'input value type should be numpy ndarray, got {type(value)}'
            assert len(values.shape) <= 3, \
                f'input array should be equal to or less than 3 dimensions, got {len(values.shape)}'

            if len(values.shape) == 1:
                values = values.reshape(1, 1, values.shape[0])
            elif len(values.shape) == 2:
                values = values.reshape(1, *values.shape)
            self._l_count, self._r_count, self._c_count = values.shape
            self._values = values
            self._is_empty = False
            if levels is None:
                levels = range(self._l_count)
                self._levels = dict(zip(levels, levels))
            else:
                self._levels = _labels_to_dict(levels, range(self._l_count))

            if rows is None:
                rows = range(self._r_count)
                self._rows = dict(zip(rows, rows))
            else:
                self._rows = _labels_to_dict(rows, range(self._r_count))

            if columns is None:
                columns = range(self._c_count)
                self._columns = dict(zip(columns, columns))
            else:
                self._columns = _labels_to_dict(columns, range(self._c_count))

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
            self._levels = _labels_to_dict(input_shares, self.shares)

    @property
    def level_count(self):
        return self._l_count

    @property
    def rows(self):
        return self._rows

    @property
    def hdates(self):
        if self.is_empty:
            return 0
        else:
            return list(self._rows.keys())

    @hdates.setter
    def hdates(self, input_hdates):
        if not self.is_empty:
            self._rows = _labels_to_dict(input_hdates, self.hdates)

    @property
    def row_count(self):
        return self._r_count

    @property
    def htypes(self):
        if self.is_empty:
            return 0
        else:
            return list(self._columns.keys())

    @htypes.setter
    def htypes(self, input_htypes):
        if not self.is_empty:
            self._columns = _labels_to_dict(input_htypes, self.htypes)

    @property
    def columns(self):
        return self._columns

    @property
    def column_count(self):
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
            htype_slice = _list_or_slice(htype_slice, self.columns)
            share_slice = _list_or_slice(share_slice, self.levels)
            hdate_slice = _list_or_slice(hdate_slice, self.rows)

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

    def fillna(self, with_val):
        """ 使用with_value来填充HistoryPanel中的所有nan值

        :param with_val:
        :return:
        """
        if not self.is_empty:
            np._values = np.where(np.isnan(self._values), with_val, self._values)
        return self


    # TODO implement this method
    def join(self,
             other,
             same_shares:bool = False,
             same_htypes:bool = False,
             same_hdates:bool = False,
             fill_value:float = np.nan):
        """ Join one historypanel object with another one

        :param same_shares:
        :param same_htypes:
        :param same_hdates:
        :param fill_value:
        :param other: type: HistoryPanel
        :return:
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
                        combined_hdate_id = _labels_to_dict(combined_hdates, combined_hdates)
                        this_hdate_id = _labels_to_dict(this_hdates, this_hdates)
                        other_hdate_id = _labels_to_dict(other_hdates, other_hdates)
                        if hdate in this_hdates:
                            combined_values[:, combined_hdate_id[hdate], :] = self.values[:, this_hdate_id[hdate], :]
                        else:
                            combined_values[:, combined_hdate_id[hdate], :] = other.values[:, other_hdate_id[hdate], :]

                elif same_hdates:
                    for htype in combined_htypes:
                        combined_htype_id = _labels_to_dict(combined_htypes, combined_htypes)
                        this_htype_id = _labels_to_dict(this_htypes, this_htypes)
                        other_htype_id = _labels_to_dict(other_htypes, other_htypes)
                        if htype in this_htypes:
                            combined_values[:, :, combined_htype_id[htype]] = self.values[:, :, this_htype_id[htype]]
                        else:
                            combined_values[:, :, combined_htype_id[htype]] = other.values[:, :, other_htype_id[htype]]
                else:
                    for hdate in combined_hdates:
                        for htype in combined_htypes:
                            combined_hdate_id = _labels_to_dict(combined_hdates, combined_hdates)
                            this_hdate_id = _labels_to_dict(this_hdates, this_hdates)
                            other_hdate_id = _labels_to_dict(other_hdates, other_hdates)
                            combined_htype_id = _labels_to_dict(combined_htypes, combined_htypes)
                            this_htype_id = _labels_to_dict(this_htypes, this_htypes)
                            other_htype_id = _labels_to_dict(other_htypes, other_htypes)
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

    # TODO implement this method
    def as_type(self, dtype):
        """ Convert the data type of current HistoryPanel to another

        :param dtype:
        :return:
        """
        raise NotImplementedError

    def to_dataframe(self, htype: str = None, share: str = None) -> pd.DataFrame:
        if self.is_empty:
            return pd.DataFrame()
        else:
            if htype is not None:
                v = self[htype].T.squeeze()
                return pd.DataFrame(v, index=self.hdates, columns=self.shares)
            if share is not None:
                v = self[:, share].squeeze()
                return pd.DataFrame(v, index=self.hdates, columns=self.htypes)

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


def _list_or_slice(unknown_input, str_int_dict):
    """ 将输入的item转化为slice或数字列表的形式,用于生成HistoryPanel的数据切片：

    1，当输入item为slice时，直接返回slice
    2 输入数据为string, 根据string的分隔符类型确定选择的切片：
        2.1, 当字符串不包含分隔符时，直接输出对应的单片数据, 如'close'输出为[0]
        2.2, 当字符串以逗号分隔时，输出每个字段对应的切片，如'close,open', 输出[0, 2]
        2.3, 当字符串以冒号分割时，输出第一个字段起第二个字段止的切片，如'close:open',输出[0:2] -> [0,1,2]
    3 输入数据为列表时，检查列表元素的类型（不支持混合数据类型的列表如['close', 1, True]）：
        3.1 如果列表元素为string，输出每个字段名对应的列表编号，如['close','open'] 输出为 [0,2]
        3.2 如果列表元素为int时，输出对应的列表编号，如[0,1,3] 输出[0,1,3]
        3.3 如果列表元素为boolean时，输出True对应的切片编号，如[True, True, False, False] 输出为[0,1]
    4 输入数据为int型时，输出相应的切片，如输入0的输出为[0]

    :param unknown_input: slice or int/str or list of int/string
    :param str_int_dict: a dictionary that contains strings as keys and integer as values
    :return:
        a list of slice/list that can be used to slice the Historical Data Object
    """
    if isinstance(unknown_input, slice):
        return unknown_input  # slice object can be directly used
    elif isinstance(unknown_input, int):  # number should be converted to a list containing itself
        return np.array([unknown_input])
    elif isinstance(unknown_input, str):  # string should be converted to numbers
        string_input = unknown_input
        if string_input.find(',') > 0:
            string_list = _str_to_list(input_string=string_input, sep_char=',')
            res = []
            for string in string_list:
                res.append(str_int_dict[string])
            return np.array(res)
        elif string_input.find(':') > 0:
            start_end_strings = _str_to_list(input_string=string_input, sep_char=':')
            start = str_int_dict[start_end_strings[0]]
            end = str_int_dict[start_end_strings[1]]
            if start > end:
                start, end = end, start
            return np.arange(start, end + 1)
        else:
            return [str_int_dict[string_input]]
    elif isinstance(unknown_input, list):
        is_list_of_str = isinstance(unknown_input[0], str)
        is_list_of_int = isinstance(unknown_input[0], int)
        is_list_of_bool = isinstance(unknown_input[0], bool)
        if is_list_of_bool:
            return np.array(str_int_dict.values())[unknown_input]
        else:
            res = []
            for list_item in unknown_input:  # convert all items into a number:
                if is_list_of_str:
                    res.append(str_int_dict[list_item])
                elif is_list_of_int:
                    res.append(list_item)
                else:
                    return None
            return np.array(res)
    else:
        return None


def _labels_to_dict(input_labels, target_list):
    """ 给target_list中的元素打上标签，建立标签-元素序号映射以方便通过标签访问元素

    根据输入的参数生成一个字典序列，这个字典的键为input_labels中的内容，值为一个[0~N]的range，且N=target_list中的元素的数量
    这个函数生成的字典可以生成一个适合快速访问的label与target_list中的元素映射，使得可以快速地通过label访问列表中的元素
    例如，列表target_list 中含有三个元素，分别是[100, 130, 170]
    现在输入一个label清单，作为列表中三个元素的标签，分别为：['first', 'second', 'third']
    使用labels_to_dict函数生成一个字典ID如下：
    ID:  {'first' : 0
         'second': 1
         'third' : 2}
    通过这个字典，可以容易且快速地使用标签访问target_list中的元素：
    target_list[ID['first']] == target_list[0] == 100

    本函数对输入的input_labels进行合法性检查，确保input_labels中没有重复的标签，且标签的数量与target_list相同
    :param input_labels: 输入标签，可以接受两种形式的输入：
                                    字符串形式: 如:     'first,second,third'
                                    列表形式，如:      ['first', 'second', 'third']
    :param target_list: 需要
    :return:
    """
    if isinstance(input_labels, str):
        input_labels = _str_to_list(input_string=input_labels)
    unique_count = len(set(input_labels))
    assert len(input_labels) == unique_count, \
        f'InputError, label duplicated, count of target list is {len(target_list)},' \
        f' got {unique_count} unique labels only.'
    assert unique_count == len(target_list), \
        f'InputError, length of input labels does not equal to that of target list, expect ' \
        f'{len(target_list)}, got {unique_count} unique labels instead.'
    return dict(zip(input_labels, range(len(target_list))))


def _str_to_list(input_string, sep_char: str = ','):
    """将逗号或其他分割字符分隔的字符串序列去除多余的空格后分割成字符串列表，分割字符可自定义"""
    assert isinstance(input_string, str), f'InputError, input is not a string!, got {type(input_string)}'
    res = input_string.replace(' ', '').split(sep_char)
    return res


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

# TODO: implement this function first!
def hp_join(*historypanels):
    """ join *historypanels into one history panel if they are not None

    :param historypanels:
    :return:
    """
    raise NotImplementedError

def dataframe_to_hp(df: pd.DataFrame,
                    hdates=None,
                    htypes=None,
                    shares=None,
                    column_type: str = 'share') -> HistoryPanel:
    """ 根据DataFrame中的数据创建历史数据板HistoryPanel对象

    :param df: pd.DataFrame, 需要被转化为HistoryPanel的DataFrame
    :param hdates:
    :param htypes: str,
    :param shares: str,
    :param column_type: str: 可以为'share' or 'htype'
    :return:
        HistoryPanel对象
    """
    from collections import Iterable
    assert isinstance(df, pd.DataFrame), f'Input df should be pandas DataFrame! got {type(df)} instead.'
    if hdates is None:
        hdates = df.index
    assert isinstance(hdates, Iterable), f'TypeError, hdates should be iterable, got {type(hdates)} instead.'
    index_count = len(hdates)
    assert index_count == len(df.index), \
        f'InputError, can not match {index_count} indices with {len(df.hdates)} rows of DataFrame'
    if column_type.lower() == 'share':
        if shares is None:
            shares = df.columns
        elif isinstance(shares, str):
            shares = shares.split(',')
            print(shares)
            assert len(shares) == len(df.columns), \
                f'InputError, can not match {len(shares)} shares with {len(df.columns)} columns of DataFrame'
        else:
            assert isinstance(shares, Iterable), f'TypeError: levels should be iterable, got {type(shares)} instead.'
            assert len(shares) == len(df.columns), \
                f'InputError, can not match {len(shares)} shares with {len(df.columns)} columns of DataFrame'
        assert htypes is not None, f'InputError, htypes should be given when they can not inferred'
        assert isinstance(htypes, str), \
            f'TypeError, data type of dtype should be a string, got {type(htypes)} instead.'
        share_count = len(shares)
        history_panel_value = np.zeros(shape=(share_count, len(hdates), 1))
        for i in range(share_count):
            history_panel_value[i, :, 0] = df.values[:, i]
    else:
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
    表示把数据框按照股票方式组合，假定每个数据框代表一个share的数据，每一列代表一个htype。组合后的HP对象
    层数与数据框的数量相同，而列数等于所有数据框的列的并集，行标签也为所有数据框的行标签的并集
    在这种模式下，shares参数必须给出，且shares的数量必须与数据框的数量相同
    stack_along == 'htypes'，
    表示把数据框按照股票方式组合，假定每个数据框代表一个htype的数据，每一列代表一个share。组合后的HP对象
    列数与数据框的数量相同，而层数等于所有数据框的列的并集，行标签也为所有数据框的行标签的并集
    在这种模式下，htypes参数必须给出，且htypes的数量必须与数据框的数量相同

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
        assert isinstance(shares, list)
        assert len(shares) == len(dfs)
        combined_shares.extend(shares)
    else:
        assert htypes is not None
        assert isinstance(htypes, list)
        assert len(htypes) == len(dfs)
        combined_htypes.extend(htypes)
    for df in dfs:
        assert isinstance(df, pd.DataFrame), \
            f'InputError, dfs should be a list of pandas DataFrame, got {type(df)} instead.'
        combined_index.extend(pd.to_datetime(df.index.values))
        if stack_along == 'shares':
            combined_htypes.extend(df.columns)
        else:
            combined_shares.extend(df.columns)
    if stack_along == 'shares':
        combined_htypes = list(set(combined_htypes))
    else:
        combined_shares = list(set(combined_shares))
    combined_index = list(set(combined_index))
    htype_count = len(combined_htypes)
    share_count = len(combined_shares)
    index_count = len(combined_index)
    combined_htypes_dict = dict(zip(combined_htypes, range(htype_count)))
    combined_shares_dict = dict(zip(combined_shares, range(share_count)))
    combined_index.sort()
    res_values = np.zeros(shape=(share_count, index_count, htype_count))
    res_values.fill(np.nan)
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

def get_history_panel(start, end, freq, shares, htypes, chanel):
    """ 最主要的历史数据获取函数，从本地（数据库/csv/hd5）或者在线（Historical Utility functions）获取所需的数据并组装为适应与策略
        需要的HistoryPanel数据对象

        首先利用不同的get_X_type_raw_data()函数获取不同类型的原始数据，再把原始数据整理成为date_by_row及htype_by_column的不同的
        dataframe，再使用stack_dataframe()函数把所有的dataframe组合成HistoryPanel格式

    :param start:
    :param end:
    :param shares:
    :param htypes:
    :param chanel:
    :return:
    """
    assert isinstance(htypes, str), f'InputError, htypes should be a string, got {type(htypes)}'
    htypes = _str_to_list(input_string=htypes, sep_char=',')
    assert isinstance(shares, str), f'InputError, share should be a string, got {type(shares)}'
    price_type_data = []
    financial_type_data = []
    composite_type_data = []
    dataframes_to_stack = []
    for htype in htypes:
        if htype in PRICE_TYPE_DATA:
            price_type_data.append(htype)
        elif htype in FINANCIAL_REPORT_TYPE_DATA:
            financial_type_data.append(htype)
        elif htype in COMPOSIT_TYPE_DATA:
            composite_type_data.append(htype)
        else:
            raise TypeError(f'{htype} is an unknown data type!')
    result_hp=HistoryPanel()
    if len(price_type_data) > 0:
        print('Getting price type historical data...')
        # print(f'In get history panel() function, price type data are \n{price_type_data}, \nshares are\n {shares}'
        #       f'\n start date is {start}, type {type(start)}, \n end date is {end}, type {type(end)}')
        dataframes_to_stack.extend(get_price_type_raw_data(start=start,
                                                           end=end,
                                                           freq=freq,
                                                           shares=shares,
                                                           htypes=price_type_data,
                                                           chanel=chanel))
        result_hp = result_hp.join(other=stack_dataframes(dfs=dataframes_to_stack,
                                                          stack_along='shares',
                                                          shares=_str_to_list(shares)),
                                   same_shares=True)

    if len(financial_type_data) > 0:
        print('Getting financial report...')
        # print(f'In get history panel() function, financial type data are \n{financial_type_data}, \n'
        #       f'shares are\n {shares}')
        dataframes_to_stack = get_financial_report_type_raw_data(start=start,
                                                                 end=end,
                                                                 shares=shares,
                                                                 htypes=financial_type_data,
                                                                 chanel=chanel)
        result_hp = result_hp.join(other=stack_dataframes(dfs=dataframes_to_stack,
                                                          stack_along='shares',
                                                          shares=_str_to_list(shares)),
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
                                                          shares=_str_to_list(shares)),
                                   same_shares=True)

    # ============= 调试代码 :=============
    '''
    print(f'in function get_history_panel(), history panels are generated, they are:\n')
    if price_type_hp is not None:
        print(f'price type history panel: \n{price_type_hp.info()}')
    if financial_type_hp is not None:
        print(f'financial type history panel: \n{financial_type_hp.info()}')
    if composite_type_hp is not None:
        print(f'composite type history panel:\n{composite_type_hp.info()}')
    '''
    return result_hp

def get_price_type_raw_data(start: str,
                            end: str,
                            freq: str,
                            shares: str,
                            htypes: str,
                            chanel:str = 'online'):
    """ 在线获取普通类型历史数据，并且打包成包含date_by_row且htype_by_column的dataframe的列表

    :param start:
    :param end:
    :param freq:
    :param shares:
    :param htypes:
    :param chanel: str: {'online', 'local'}
                    chanel == 'online' 从网络获取历史数据
                    chanel == 'local'  从本地数据库获取历史数据
    :return:
    """
    if htypes is None:
        htypes = PRICE_TYPE_DATA
    if isinstance(htypes, str):
        htypes = _str_to_list(input_string=htypes, sep_char=',')
    raw_df = get_bar(share=shares, start=start, end=end, freq=freq)
    # print('raw df before rearange\n', raw_df)
    raw_df.drop_duplicates(subset=['ts_code', 'trade_date'], inplace=True)
    raw_df.index = range(len(raw_df))
    # print('\nraw df after rearange\n', raw_df)
    df_per_share = []
    shares = _str_to_list(input_string=shares, sep_char=',')
    for share in shares:
        df_per_share.append(raw_df.loc[np.where(raw_df.ts_code == share)])
    columns_to_remove = list(set(PRICE_TYPE_DATA) - set(htypes))
    for df in df_per_share:
        df.index = pd.to_datetime(df.trade_date)
        df.drop(columns=columns_to_remove, inplace=True)
        df.drop(columns=['ts_code', 'trade_date'], inplace=True)
    return df_per_share

def get_financial_report_type_raw_data(start, end, shares, htypes, chanel:str = 'online'):
    """ 在线获取财报类历史数据

    :param start:
    :param end:
    :param shares:
    :param htypes:
    :param chanel:
    :return:
    """
    if isinstance(htypes, str):
        htypes = _str_to_list(input_string=htypes, sep_char=',')
    report_fields = ['ts_code', 'f_ann_date']
    report_fields.extend(htypes)
    # print('htypes',htypes, "\nreport fields: ", report_fields)
    raw_df = income(start=start, end=end, ts_code=shares, fields=report_fields)
    # print('raw df before rearange\n', raw_df)
    raw_df.drop_duplicates(subset=['ts_code', 'f_ann_date'], inplace=True)
    raw_df.index = range(len(raw_df))
    # print('\nraw df after rearange\n', raw_df)
    df_per_share = []
    shares = _str_to_list(input_string=shares, sep_char=',')
    for share in shares:
        df_per_share.append(raw_df.loc[np.where(raw_df.ts_code == share)])
    for df in df_per_share:
        # print('\nsingle df of share before removal\n', df)
        df.index = pd.to_datetime(df.f_ann_date)
        df.index.name = 'date'
        df.drop(columns=['ts_code', 'f_ann_date'], inplace=True)
        # print('\nsingle df of share after removal\n', df)
    return df_per_share

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

# ==================
# Historical Utility functions based on tushare
# ==================

# Basic Market Data
# ==================

def stock_basic(is_hs: str = None,
                list_status: str = None,
                exchange: str = None,
                fields: str = None):
    """ 获取基础信息数据，包括股票代码、名称、上市日期、退市日期等

    :param is_hs: optinal, 是否沪深港通标的，N否 H沪股通 S深股通
    :param list_status: optional, 上市状态： L上市 D退市 P暂停上市
    :param exchange: optional, 交易所 SSE上交所 SZSE深交所 HKEX港交所(未上线)
    :param fields: 逗号分隔的字段名称字符串，可选字段包括输出参数中的任意组合
    :return: pd.DataFrame:
        column      type    description
        ts_code,    str,    TS代码
        symbol,     str,    股票代码
        name,       str,    股票名称
        area,       str,    所在地域
        industry,   str,    所属行业
        fullname,   str,    股票全称
        ennamem     str,    英文全称
        market,     str,    市场类型 （主板/中小板/创业板/科创板）
        exchange,   str,    交易所代码
        curr_type,  str,    交易货币
        list_status,str,    上市状态： L上市 D退市 P暂停上市
        list_date,  str,    上市日期
        delist_date,str,    退市日期
        is_hs,      str,    是否沪深港通标的，N否 H沪股通 S深股通
    """
    if is_hs is None: is_hs = ''
    if list_status is None: list_status = 'L'
    if exchange is None: exchange = ''
    if fields is None: fields = 'ts_code,symbol,name,area,industry,list_date'
    pro = ts.pro_api()
    return pro.stock_basic(exchange=exchange,
                           list_status=list_status,
                           is_hs=is_hs,
                           fields=fields)


def trade_calendar(exchange: str = 'SSE',
                   start: str = None,
                   end: str = None,
                   is_open: str = None):
    """ 获取各大交易所交易日历数据,默认提取的是上交所

    :param exchange: 交易所 SSE上交所,SZSE深交所,CFFEX 中金所,SHFE 上期所,CZCE 郑商所,DCE 大商所,INE 上能源,IB 银行间,XHKG 港交所
    :param start: 开始日期
    :param end: 结束日期
    :param is_open: 是否交易 '0'休市 '1'交易
    :return: pd.DataFrame
        column          type    description
        exchange,       str,    交易所 SSE上交所 SZSE深交所
        cal_date,       str,    日历日期
        is_open,        str,    是否交易 0休市 1交易
        pretrade_date,  str,    默认不显示，  上一个交易日
    """
    pro = ts.pro_api()
    return pro.trade_cal(exchange=exchange,
                         start_date=start,
                         end_date=end,
                         is_open=is_open)


def name_change(ts_code: str = None,
                start: str = None,
                end: str = None,
                fields: str = None):
    """ 历史名称变更记录

    :param ts_code:
    :param start:
    :param end:
    :return: pd.DataFrame
        column              type    default     description
        ts_code	            str	    Y	        TS代码
        name	            str	    Y	        证券名称
        start_date	        str	    Y	        开始日期
        end_date	        str	    Y	        结束日期
        ann_date	        str	    Y	        公告日期
        change_reason	    str	    Y	        变更原因
    example:
        pro = ts.pro_api()
        df = pro.namechange(ts_code='600848.SH',
                            fields='ts_code,name,start_date,end_date,change_reason')
    :output:
                ts_code     name      start_date   end_date      change_reason
        0       600848.SH   上海临港   20151118      None           改名
        1       600848.SH   自仪股份   20070514     20151117         撤销ST
        2       600848.SH   ST自仪     20061026    20070513         完成股改
        3       600848.SH   SST自仪   20061009     20061025        未股改加S
        4       600848.SH   ST自仪     20010508    20061008         ST
        5       600848.SH   自仪股份  19940324      20010507         其他
    """
    if fields is None: fields = 'ts_code,name,start,end,change_reason'
    pro = ts.pro_api()
    return pro.namechange(ts_code=ts_code,
                          start_date=start,
                          end_date=end,
                          fields=fields)


def new_share(start: str = None,
              end: str = None) -> pd.DataFrame:
    """

    :param start: str, 上网发行开始日期
    :param end: str, 上网发行结束日期
    :return: pd.DataFrame
        column              type    default     description
        ts_code		        str	    Y	        TS股票代码
        sub_code	        str	    Y	        申购代码
        name		        str	    Y	        名称
        ipo_date	        str	    Y	        上网发行日期
        issue_date	        str	    Y	        上市日期
        amount		        float	Y	        发行总量（万股）
        market_amount	    float	Y	        上网发行总量（万股）
        price		        float	Y	        发行价格
        pe		            float	Y	        市盈率
        limit_amount	    float	Y	        个人申购上限（万股）
        funds		        float	Y	        募集资金（亿元）
        ballot		        float	Y	        中签率
    example:
        pro = ts.pro_api()
        df = pro.new_share(start_date='20180901', end='20181018')
    output:
            ts_code     ub_code  name  ipo_date    issue_date   amount  market_amount  \
        0   002939.SZ   002939  长城证券  20181017       None  31034.0        27931.0
        1   002940.SZ   002940   昂利康  20181011   20181023   2250.0         2025.0
        2   601162.SH   780162  天风证券  20181009   20181019  51800.0        46620.0
        3   300694.SZ   300694  蠡湖股份  20180927   20181015   5383.0         4845.0
        4   300760.SZ   300760  迈瑞医疗  20180927   20181016  12160.0        10944.0
        5   300749.SZ   300749  顶固集创  20180913   20180925   2850.0         2565.0
        6   002937.SZ   002937  兴瑞科技  20180912   20180926   4600.0         4140.0
        7   601577.SH   780577  长沙银行  20180912   20180926  34216.0        30794.0
        8   603583.SH   732583  捷昌驱动  20180911   20180921   3020.0         2718.0
        9   002936.SZ   002936  郑州银行  20180907   20180919  60000.0        54000.0
        10  300748.SZ   300748  金力永磁  20180906   20180921   4160.0         3744.0
        11  603810.SH   732810  丰山集团  20180906   20180917   2000.0         2000.0
        12  002938.SZ   002938  鹏鼎控股  20180905   20180918  23114.0        20803.0

            price     pe  limit_amount   funds  ballot
        0    6.31  22.98          9.30  19.582    0.16
        1   23.07  22.99          0.90   5.191    0.03
        2    1.79  22.86         15.50   0.000    0.25
        3    9.89  22.98          2.15   5.324    0.04
        4   48.80  22.99          3.60  59.341    0.08
        5   12.22  22.99          1.10   3.483    0.03
        6    9.94  22.99          1.80   4.572    0.04
        7    7.99   6.97         10.20  27.338    0.17
        8   29.17  22.99          1.20   8.809    0.03
        9    4.59   6.50         18.00  27.540    0.25
        10   5.39  22.98          1.20   2.242    0.05
        11  25.43  20.39          2.00   5.086    0.02
        12  16.07  22.99          6.90  37.145    0.12
    """
    pro = ts.pro_api()
    return pro.new_share(start_date=start, end_date=end)


def stock_company(ts_code: str = None,
                  exchange: str = None,
                  fields: str = None) -> pd.DataFrame:
    """

    :param ts_code: str, 股票代码
    :param exchange: str, 交易所代码 ，SSE上交所 SZSE深交所
    :param fields: str, 逗号分隔的字段名称字符串，可选字段包括输出参数中的任意组合
    :return: pd.DataFrame
        column              type    default     description
        ts_code		        str	    Y	        股票代码
        exchange	        str	    Y	        交易所代码 ，SSE上交所 SZSE深交所
        chairman	        str	    Y	        法人代表
        manager		        str	    Y	        总经理
        secretary	        str	    Y	        董秘
        reg_capital	        float	Y	        注册资本
        setup_date	        str	    Y	        注册日期
        province	        str	    Y	        所在省份
        city		        str	    Y	        所在城市
        introduction	    str	    N	        公司介绍
        website		        str	    Y	        公司主页
        email		        str	    Y	        电子邮件
        office		        str	    N	        办公室
        employees	        int	    Y	        员工人数
        main_business	    str	    N	        主要业务及产品
        business_scope	    str	    N	        经营范围
    example:
        stock_company(exchange='SZSE',
                      fields='ts_code,chairman,manager,secretary,reg_capital,setup_date,province')
    output:
               ts_code     chairman manager     secretary   reg_capital setup_date province  \
        0     000001.SZ      谢永林     胡跃飞        周强  1.717041e+06   19871222       广东
        1     000002.SZ       郁亮     祝九胜        朱旭  1.103915e+06   19840530       广东
        2     000003.SZ      马钟鸿     马钟鸿        安汪  3.334336e+04   19880208       广东
        3     000004.SZ      李林琳     李林琳       徐文苏  8.397668e+03   19860505       广东
        4     000005.SZ       丁芃     郑列列       罗晓春  1.058537e+05   19870730       广东
        5     000006.SZ      赵宏伟     朱新宏        杜汛  1.349995e+05   19850525       广东
        6     000007.SZ      智德宇     智德宇       陈伟彬  3.464480e+04   19830311       广东
        7     000008.SZ      王志全      钟岩       王志刚  2.818330e+05   19891011       北京
        8     000009.SZ      陈政立     陈政立       郭山清  2.149345e+05   19830706       广东
        9     000010.SZ       曾嵘     李德友       金小刚  8.198547e+04   19881231       广东
        10    000011.SZ      刘声向     王航军       范维平  5.959791e+04   19830117       广东
    """
    if fields is None: fields = 'ts_code,chairman,manager,secretary,reg_capital,setup_date,province'
    pro = ts.pro_api()
    return pro.stock_comapany(ts_code=ts_code, exchange=exchange, fields=fields)


# Bar price data
# ==================

def get_bar(share: str,
            start: str,
            end: str,
            asset_type: str = 'E',
            adj: str = 'None',
            freq: str = 'D',
            ma: list = None) -> pd.DataFrame:
    """ get historical prices with rehabilitation rights
    获取指数或股票的复权历史价格

    input:
    :param share: str, 证券代码
    :param start: str, 开始日期 (格式：YYYYMMDD)
    :param end: str, 结束日期 (格式：YYYYMMDD)
    :param asset_type: str, 资产类别：E股票 I沪深指数 C数字货币 F期货 FD基金 O期权，默认E
    :param adj: str, 复权类型(只针对股票)：None未复权 qfq前复权 hfq后复权 , 默认None
    :param freq: str, 数据频度 ：1MIN表示1分钟（1/5/15/30/60分钟） D日线 ，默认D
    :param ma: str, 均线，支持任意周期的均价和均量，输入任意合理int数值
    return: pd.DataFrame
    column          type    description
    ts_code         str     证券代码
    trade_date      str     交易日期，格式YYYYMMDD
    open            float   开盘价
    high            float   最高价
    low             float   最低价
    close           float   收盘价
    pre_close       float   前一收盘价
    change          float   收盘价涨跌
    pct_chg         float   收盘价涨跌百分比
    vol             float   交易量
    amount          float   交易额
    example:
    获取日k线数据，前复权：
    get_bar(share='000001.SZ', adj='qfq', start_date='20180101', end_date='20181011')
    获取周K线数据，后复权：
    get_bar(share='000001.SZ', freq='W', adj='hfq', start_date='20180101', end_date='20181011')
    output:
    前复权日K线数据
           ts_code trade_date     open     high      low    close  pre_close  change  pct_chg         vol       amount
    0    000001.SZ   20181011  10.0500  10.1600   9.7000   9.8600    10.4500 -0.5900  -5.6459  1995143.83  1994186.611
    1    000001.SZ   20181010  10.5400  10.6600  10.3800  10.4500    10.5600 -0.1100  -1.0417   995200.08  1045666.180
    2    000001.SZ   20181009  10.4600  10.7000  10.3900  10.5600    10.4500  0.1100   1.0526  1064084.26  1117946.550
    3    000001.SZ   20181008  10.7000  10.7900  10.4500  10.4500    11.0500 -0.6000  -5.4299  1686358.52  1793455.283
    4    000001.SZ   20180928  10.7800  11.2700  10.7800  11.0500    10.7400  0.3100   2.8864  2110242.67  2331358.288
    """
    assert isinstance(share, str), 'TypeError: share code should be a string'
    return ts.pro_bar(ts_code=share,
                      start_date=start,
                      end_date=end,
                      asset=asset_type,
                      adj=adj,
                      freq=freq,
                      ma=ma)


# Finance Data
# ================

def income(ts_code: str,
           rpt_date: str = None,
           start: str = None,
           end: str = None,
           period: str = None,
           report_type: str = None,
           comp_type: str = None,
           fields: str = None) -> pd.DataFrame:
    """ 获取上市公司财务利润表数据

    :rtype: pd.DataFrame
    :param ts_code: 股票代码
    :param rpt_date: optional 公告日期
    :param start: optional 公告开始日期
    :param end: optional 公告结束日期
    :param period: optional 报告期(每个季度最后一天的日期，比如20171231表示年报)
    :param report_type: optional 报告类型： 参考下表说明
    :param comp_type: optional 公司类型：1一般工商业 2银行 3保险 4证券
    :param fields: str, 输出数据，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame:
        column              type   dft  description
        ts_code	            str	    Y   TS代码
        ann_date	        str	    Y	公告日期
        f_ann_date	        str	    Y	实际公告日期
        end	        str	    Y	报告期
        report_type	        str	    Y	报告类型 1合并报表                  上市公司最新报表（默认）
                                                2单季合并                  单一季度的合并报表
                                                3调整单季合并表            调整后的单季合并报表（如果有）
                                                4调整合并报表             本年度公布上年同期的财务报表数据，报告期为上年度
                                                5调整前合并报表            数据发生变更，将原数据进行保留，即调整前的原数据
                                                6母公司报表              该公司母公司的财务报表数据
                                                7母公司单季表             母公司的单季度表
                                                8 母公司调整单季表         母公司调整后的单季表
                                                9母公司调整表             该公司母公司的本年度公布上年同期的财务报表数据
                                                10母公司调整前报表          母公司调整之前的原始财务报表数据
                                                11调整前合并报表           调整之前合并报表原数据
                                                12母公司调整前报表          母公司报表发生变更前保留的原数据
        comp_type	        str	    Y	公司类型(1一般工商业2银行3保险4证券)
        basic_eps	        float	Y	基本每股收益
        diluted_eps	        float	Y	稀释每股收益
        total_revenue	    float	Y	营业总收入
        revenue	            float	Y	营业收入
        int_income	        float	Y	利息收入
        prem_earned	        float	Y	已赚保费
        comm_income	        float	Y	手续费及佣金收入
        n_commis_income	    float	Y	手续费及佣金净收入
        n_oth_income	    float	Y	其他经营净收益
        n_oth_b_income	    float	Y	加:其他业务净收益
        prem_income	        float	Y	保险业务收入
        out_prem	        float	Y	减:分出保费
        une_prem_reser	    float	Y	提取未到期责任准备金
        reins_income	    float	Y	其中:分保费收入
        n_sec_tb_income	    float	Y	代理买卖证券业务净收入
        n_sec_uw_income	    float	Y	证券承销业务净收入
        n_asset_mg_income	float	Y	受托客户资产管理业务净收入
        oth_b_income	    float	Y	其他业务收入
        fv_value_chg_gain	float	Y	加:公允价值变动净收益
        invest_income	    float	Y	加:投资净收益
        ass_invest_income	float	Y	其中:对联营企业和合营企业的投资收益
        forex_gain	        float	Y	加:汇兑净收益
        total_cogs	        float	Y	营业总成本
        oper_cost	        float	Y	减:营业成本
        int_exp	            float	Y	减:利息支出
        comm_exp	        float	Y	减:手续费及佣金支出
        biz_tax_surchg	    float	Y	减:营业税金及附加
        sell_exp	        float	Y	减:销售费用
        admin_exp	        float	Y	减:管理费用
        fin_exp	            float	Y	减:财务费用
        assets_impair_loss	float	Y	减:资产减值损失
        prem_refund	        float	Y	退保金
        compens_payout	    float	Y	赔付总支出
        reser_insur_liab	float	Y	提取保险责任准备金
        div_payt	        float	Y	保户红利支出
        reins_exp	        float	Y	分保费用
        oper_exp	        float	Y	营业支出
        compens_payout_refu	float	Y	减:摊回赔付支出
        insur_reser_refu	float	Y	减:摊回保险责任准备金
        reins_cost_refund	float	Y	减:摊回分保费用
        other_bus_cost	    float	Y	其他业务成本
        operate_profit	    float	Y	营业利润
        non_oper_income	    float	Y	加:营业外收入
        non_oper_exp	    float	Y	减:营业外支出
        nca_disploss	    float	Y	其中:减:非流动资产处置净损失
        total_profit	    float	Y	利润总额
        income_tax	        float	Y	所得税费用
        n_income	        float	Y	净利润(含少数股东损益)
        n_income_attr_p	    float	Y	净利润(不含少数股东损益)
        minority_gain	    float	Y	少数股东损益
        oth_compr_income	float	Y	其他综合收益
        t_compr_income	    float	Y	综合收益总额
        compr_inc_attr_p	float	Y	归属于母公司(或股东)的综合收益总额
        compr_inc_attr_m_s	float	Y	归属于少数股东的综合收益总额
        ebit	            float	Y	息税前利润
        ebitda	            float	Y	息税折旧摊销前利润
        insurance_exp	    float	Y	保险业务支出
        undist_profit	    float	Y	年初未分配利润
        distable_profit	    float	Y	可分配利润
        update_flag	        str	    N	更新标识，0未修改1更正过
    :example
        income(ts_code='600000.SH', start_date='20180101',
               end='20180730',
               fields='ts_code,ann_date,f_ann_date,end,report_type,comp_type,basic_eps,diluted_eps')
    """
    if fields is None: fields = 'ts_code,rpt_date,f_ann_date,end,report_type,comp_type,basic_eps,diluted_eps'
    pro = ts.pro_api()
    return pro.income(ts_code=ts_code,
                      ann_date=rpt_date,
                      start_date=start,
                      end_date=end,
                      period=period,
                      report_type=report_type,
                      comp_type=comp_type,
                      fields=fields)


def balance(ts_code: str,
            rpt_date: str = None,
            start: str = None,
            end: str = None,
            period: str = None,
            report_type: str = None,
            comp_type: str = None,
            fields: str = None) -> pd.DataFrame:
    """ 获取上市公司财务数据资产负债表

    :param ts_code: 股票代码
    :param rpt_date: optional 公告日期
    :param start: optional 公告开始日期
    :param end: optional 公告结束日期
    :param period: optional 报告期(每个季度最后一天的日期，比如20171231表示年报)
    :param report_type: optional 报告类型： 参考下表说明
    :param comp_type: optional 公司类型：1一般工商业 2银行 3保险 4证券
    :param fields: str, 输出数据，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column              type    default description
        s_code			    str	        Y	TS股票代码
        ann_date		    str	        Y	公告日期
        f_ann_date		    str	        Y	实际公告日期
        end_date		    str	        Y	报告期
        report_type		    str	        Y	报表类型
        comp_type		    str	        Y	公司类型
        total_share		    float	    Y	期末总股本
        cap_rese		    float	    Y	资本公积金
        undistr_porfit		float	    Y	未分配利润
        surplus_rese		float	    Y	盈余公积金
        special_rese		float	    Y	专项储备
        money_cap		    float	    Y	货币资金
        trad_asset		    float	    Y	交易性金融资产
        notes_receiv		float	    Y	应收票据
        accounts_receiv		float	    Y	应收账款
        oth_receiv		    float	    Y  	其他应收款
        prepayment		    float	    Y	预付款项
        div_receiv		    float	    Y	应收股利
        int_receiv		    float   	Y	应收利息
        inventories		    float	    Y	存货
        amor_exp		    float	    Y	待摊费用
        nca_within_1y		float	    Y	一年内到期的非流动资产
        sett_rsrv		    float	    Y	结算备付金
        loanto_oth_bank_fi	float	    Y	拆出资金
        premium_receiv		float	    Y	应收保费
        reinsur_receiv		float	    Y	应收分保账款
        reinsur_res_receiv	float	    Y	应收分保合同准备金
        pur_resale_fa		float	    Y	买入返售金融资产
        oth_cur_assets		float	    Y	其他流动资产
        total_cur_assets	float	    Y	流动资产合计
        fa_avail_for_sale	float	    Y	可供出售金融资产
        htm_invest		    float	    Y   持有至到期投资
        lt_eqt_invest		float	    Y	长期股权投资
        invest_real_estate	float	    Y	投资性房地产
        time_deposits		float	    Y	定期存款
        oth_assets		    float	    Y	其他资产
        lt_rec			    float	    Y	长期应收款
        fix_assets		    float	    Y	固定资产
        cip			        float	    Y	在建工程
        const_materials		float	    Y	工程物资
        fixed_assets_disp	float	    Y	固定资产清理
        produc_bio_assets	float	    Y	生产性生物资产
        oil_and_gas_assets	float	    Y	油气资产
        intan_assets		float	    Y	无形资产
        r_and_d			    float	    Y	研发支出
        goodwill		    float	    Y	商誉
        lt_amor_exp		    float	    Y	长期待摊费用
        defer_tax_assets	float	    Y	递延所得税资产
        decr_in_disbur		float	    Y	发放贷款及垫款
        oth_nca			    float	    Y	其他非流动资产
        total_nca		    float	    Y	非流动资产合计
        cash_reser_cb		float	    Y	现金及存放中央银行款项
        depos_in_oth_bfi	float	    Y	存放同业和其它金融机构款项
        prec_metals		    float	    Y	贵金属
        deriv_assets		float	    Y	衍生金融资产
        rr_reins_une_prem	float	    Y	应收分保未到期责任准备金
        rr_reins_outstd_cla	float	    Y	应收分保未决赔款准备金
        rr_reins_lins_liab	float	    Y	应收分保寿险责任准备金
        rr_reins_lthins_liab	float	Y	应收分保长期健康险责任准备金
        refund_depos		float	    Y	存出保证金
        ph_pledge_loans		float	    Y	保户质押贷款
        refund_cap_depos	float	    Y	存出资本保证金
        indep_acct_assets	float	    Y	独立账户资产
        client_depos		float	    Y	其中：客户资金存款
        client_prov		    float	    Y	其中：客户备付金
        transac_seat_fee	float	    Y	其中:交易席位费
        invest_as_receiv	float	    Y	应收款项类投资
        total_assets		float	    Y	资产总计
        lt_borr			    float	    Y	长期借款
        st_borr			    float	    Y	短期借款
        cb_borr			    float	    Y	向中央银行借款
        depos_ib_deposits	float	    Y	吸收存款及同业存放
        loan_oth_bank		float	    Y	拆入资金
        trading_fl		    float	    Y	交易性金融负债
        notes_payable		float	    Y	应付票据
        acct_payable		float	    Y	应付账款
        adv_receipts		float	    Y	预收款项
        sold_for_repur_fa	float	    Y	卖出回购金融资产款
        comm_payable		float	    Y	应付手续费及佣金
        payroll_payable		float	    Y	应付职工薪酬
        taxes_payable		float	    Y	应交税费
        int_payable		    float	    Y	应付利息
        div_payable		    float	    Y	应付股利
        oth_payable		    float	    Y	其他应付款
        acc_exp			    float	    Y	预提费用
        deferred_inc		float	    Y	递延收益
        st_bonds_payable	float	    Y	应付短期债券
        payable_to_reinsurer	float	Y	应付分保账款
        rsrv_insur_cont		float	    Y	保险合同准备金
        acting_trading_sec	float	    Y	代理买卖证券款
        acting_uw_sec		float	    Y	代理承销证券款
        non_cur_liab_due_1y	float	    Y	一年内到期的非流动负债
        oth_cur_liab		float	    Y	其他流动负债
        total_cur_liab		float	    Y	流动负债合计
        bond_payable		float	    Y	应付债券
        lt_payable		    float	    Y	长期应付款
        specific_payables	float	    Y	专项应付款
        estimated_liab		float	    Y	预计负债
        defer_tax_liab		float	    Y	递延所得税负债
        defer_inc_non_cur_liab	float	Y	递延收益-非流动负债
        oth_ncl			    float	    Y	其他非流动负债
        total_ncl		    float	    Y	非流动负债合计
        depos_oth_bfi		float	    Y	同业和其它金融机构存放款项
        deriv_liab		    float	    Y	衍生金融负债
        depos			    float	    Y	吸收存款
        agency_bus_liab		float	    Y	代理业务负债
        oth_liab		    float	    Y	其他负债
        prem_receiv_adva	float	    Y	预收保费
        depos_received		float	    Y	存入保证金
        ph_invest		    float	    Y	保户储金及投资款
        reser_une_prem		float	    Y	未到期责任准备金
        reser_outstd_claims	float	    Y	未决赔款准备金
        reser_lins_liab		float	    Y	寿险责任准备金
        reser_lthins_liab	float	    Y	长期健康险责任准备金
        indept_acc_liab		float	    Y	独立账户负债
        pledge_borr		    float	    Y	其中:质押借款
        indem_payable		float	    Y	应付赔付款
        policy_div_payable	float	    Y	应付保单红利
        total_liab		    float	    Y	负债合计
        treasury_share		float	    Y	减:库存股
        ordin_risk_reser	float	    Y	一般风险准备
        forex_differ		float	    Y	外币报表折算差额
        invest_loss_unconf	float	    Y	未确认的投资损失
        minority_int		float	    Y	少数股东权益
        total_hldr_eqy_exc_min_int	float	Y	股东权益合计(不含少数股东权益)
        total_hldr_eqy_inc_min_int	float	Y	股东权益合计(含少数股东权益)
        total_liab_hldr_eqy	float	    Y	负债及股东权益总计
        lt_payroll_payable	float	    Y	长期应付职工薪酬
        oth_comp_income		float	    Y	其他综合收益
        oth_eqt_tools		float	    Y	其他权益工具
        oth_eqt_tools_p_shr	float	    Y	其他权益工具(优先股)
        lending_funds		float	    Y	融出资金
        acc_receivable		float	    Y	应收款项
        st_fin_payable		float	    Y	应付短期融资款
        payables		    float	    Y	应付款项
        hfs_assets		    float	    Y	持有待售的资产
        hfs_sales		    float	    Y	持有待售的负债
        update_flag		    str	        N	更新标识
    report types:
        code type           description
        1	合并报表	        上市公司最新报表（默认）
        2	单季合并	        单一季度的合并报表
        3	调整单季合并表	    调整后的单季合并报表（如果有）
        4	调整合并报表	    本年度公布上年同期的财务报表数据，报告期为上年度
        5	调整前合并报表	    数据发生变更，将原数据进行保留，即调整前的原数据
        6	母公司报表	    该公司母公司的财务报表数据
        7	母公司单季表	    母公司的单季度表
        8	母公司调整单季表	母公司调整后的单季表
        9	母公司调整表	    该公司母公司的本年度公布上年同期的财务报表数据
        10	母公司调整前报表	母公司调整之前的原始财务报表数据
        11	调整前合并报表 	调整之前合并报表原数据
        12	母公司调整前报表	母公司报表发生变更前保留的原数据
    example:
    df = balance(ts_code='600000.SH',
                 start_date='20180101',
                 end_date='20180730',
                 fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,cap_rese')
    """
    if fields is None: fields = 'ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,cap_rese'
    pro = ts.pro_api()
    return pro.balancesheet(ts_code=ts_code,
                            ann_date=rpt_date,
                            start_date=start,
                            end_date=end,
                            period=period,
                            report_type=report_type,
                            comp_type=comp_type,
                            fields=fields)


def cashflow(ts_code: str,
             rpt_date: str = None,
             start: str = None,
             end: str = None,
             period: str = None,
             report_type: str = None,
             comp_type: str = None,
             fields: str = None) -> pd.DataFrame:
    """ 获取上市公司财务数据现金流量表

    :param ts_code:                     股票代码
    :param rpt_date: optional           公告日期
    :param start: optional         公告开始日期
    :param end: optional           公告结束日期
    :param period: optional             报告期(每个季度最后一天的日期，比如20171231表示年报)
    :param report_type: optional        报告类型： 参考下表说明
    :param comp_type: optional          公司类型：1一般工商业 2银行 3保险 4证券
    :param fields: str,                 输出数据，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column                      type    default description
        ts_code				        str	    Y	TS股票代码
        ann_date			        str	    Y	公告日期
        f_ann_date			        str	    Y	实际公告日期
        end_date			        str	    Y	报告期
        comp_type			        str	    Y	公司类型
        report_type			        str	    Y	报表类型
        net_profit			        float	Y	净利润
        finan_exp			        float	Y	财务费用
        c_fr_sale_sg			    float	Y	销售商品、提供劳务收到的现金
        recp_tax_rends			    float	Y	收到的税费返还
        n_depos_incr_fi			    float	Y	客户存款和同业存放款项净增加额
        n_incr_loans_cb			    float	Y	向中央银行借款净增加额
        n_inc_borr_oth_fi		    float	Y	向其他金融机构拆入资金净增加额
        prem_fr_orig_contr		    float	Y	收到原保险合同保费取得的现金
        n_incr_insured_dep		    float	Y	保户储金净增加额
        n_reinsur_prem			    float	Y	收到再保业务现金净额
        n_incr_disp_tfa			    float	Y	处置交易性金融资产净增加额
        ifc_cash_incr			    float	Y	收取利息和手续费净增加额
        n_incr_disp_faas		    float	Y	处置可供出售金融资产净增加额
        n_incr_loans_oth_bank		float	Y	拆入资金净增加额
        n_cap_incr_repur		    float	Y	回购业务资金净增加额
        c_fr_oth_operate_a		    float	Y	收到其他与经营活动有关的现金
        c_inf_fr_operate_a		    float	Y	经营活动现金流入小计
        c_paid_goods_s			    float	Y	购买商品、接受劳务支付的现金
        c_paid_to_for_empl		    float	Y	支付给职工以及为职工支付的现金
        c_paid_for_taxes		    float	Y	支付的各项税费
        n_incr_clt_loan_adv		    float	Y	客户贷款及垫款净增加额
        n_incr_dep_cbob			    float	Y	存放央行和同业款项净增加额
        c_pay_claims_orig_inco		float	Y	支付原保险合同赔付款项的现金
        pay_handling_chrg		    float	Y	支付手续费的现金
        pay_comm_insur_plcy		    float	Y	支付保单红利的现金
        oth_cash_pay_oper_act		float	Y	支付其他与经营活动有关的现金
        st_cash_out_act			    float	Y	经营活动现金流出小计
        n_cashflow_act			    float	Y	经营活动产生的现金流量净额
        oth_recp_ral_inv_act		float	Y	收到其他与投资活动有关的现金
        c_disp_withdrwl_invest		float	Y	收回投资收到的现金
        c_recp_return_invest		float	Y	取得投资收益收到的现金
        n_recp_disp_fiolta		    float	Y	处置固定资产、无形资产和其他长期资产收回的现金净额
        n_recp_disp_sobu		    float	Y	处置子公司及其他营业单位收到的现金净额
        stot_inflows_inv_act		float	Y	投资活动现金流入小计
        c_pay_acq_const_fiolta		float	Y	购建固定资产、无形资产和其他长期资产支付的现金
        c_paid_invest			    float	Y	投资支付的现金
        n_disp_subs_oth_biz		    float	Y	取得子公司及其他营业单位支付的现金净额
        oth_pay_ral_inv_act		    float	Y	支付其他与投资活动有关的现金
        n_incr_pledge_loan		    float	Y	质押贷款净增加额
        stot_out_inv_act		    float	Y	投资活动现金流出小计
        n_cashflow_inv_act		    float	Y	投资活动产生的现金流量净额
        c_recp_borrow			    float	Y	取得借款收到的现金
        proc_issue_bonds		    float	Y	发行债券收到的现金
        oth_cash_recp_ral_fnc_act	float	Y	收到其他与筹资活动有关的现金
        stot_cash_in_fnc_act		float	Y	筹资活动现金流入小计
        free_cashflow			    float	Y	企业自由现金流量
        c_prepay_amt_borr		    float	Y	偿还债务支付的现金
        c_pay_dist_dpcp_int_exp		float	Y	分配股利、利润或偿付利息支付的现金
        incl_dvd_profit_paid_sc_ms	float	Y	其中:子公司支付给少数股东的股利、利润
        oth_cashpay_ral_fnc_act		float	Y	支付其他与筹资活动有关的现金
        stot_cashout_fnc_act		float	Y	筹资活动现金流出小计
        n_cash_flows_fnc_act		float	Y	筹资活动产生的现金流量净额
        eff_fx_flu_cash			    float	Y	汇率变动对现金的影响
        n_incr_cash_cash_equ		float	Y	现金及现金等价物净增加额
        c_cash_equ_beg_period		float	Y	期初现金及现金等价物余额
        c_cash_equ_end_period		float	Y	期末现金及现金等价物余额
        c_recp_cap_contrib		    float	Y	吸收投资收到的现金
        incl_cash_rec_saims		    float	Y	其中:子公司吸收少数股东投资收到的现金
        uncon_invest_loss		    float	Y	未确认投资损失
        prov_depr_assets		    float	Y	加:资产减值准备
        depr_fa_coga_dpba		    float	Y	固定资产折旧、油气资产折耗、生产性生物资产折旧
        amort_intang_assets		    float	Y	无形资产摊销
        lt_amort_deferred_exp		float	Y	长期待摊费用摊销
        decr_deferred_exp		    float	Y	待摊费用减少
        incr_acc_exp			    float	Y	预提费用增加
        loss_disp_fiolta		    float	Y	处置固定、无形资产和其他长期资产的损失
        loss_scr_fa			        float	Y	固定资产报废损失
        loss_fv_chg			        float	Y	公允价值变动损失
        invest_loss			        float	Y	投资损失
        decr_def_inc_tax_assets		float	Y	递延所得税资产减少
        incr_def_inc_tax_liab		float	Y	递延所得税负债增加
        decr_inventories		    float	Y	存货的减少
        decr_oper_payable		    float	Y	经营性应收项目的减少
        incr_oper_payable		    float	Y	经营性应付项目的增加
        others				        float	Y	其他
        im_net_cashflow_oper_act	float	Y	经营活动产生的现金流量净额(间接法)
        conv_debt_into_cap		    float	Y	债务转为资本
        conv_copbonds_due_within_1y	float	Y	一年内到期的可转换公司债券
        fa_fnc_leases			    float	Y	融资租入固定资产
        end_bal_cash			    float	Y	现金的期末余额
        beg_bal_cash			    float	Y	减:现金的期初余额
        end_bal_cash_equ		    float	Y	加:现金等价物的期末余额
        beg_bal_cash_equ		    float	Y	减:现金等价物的期初余额
        im_n_incr_cash_equ		    float	Y	现金及现金等价物净增加额(间接法)
        update_flag			        str	    N	更新标识
    report types:
        1	合并报表	            上市公司最新报表（默认）
        2	单季合并	            单一季度的合并报表
        3	调整单季合并表     	调整后的单季合并报表（如果有）
        4	调整合并报表	        本年度公布上年同期的财务报表数据，报告期为上年度
        5	调整前合并报表	        数据发生变更，将原数据进行保留，即调整前的原数据
        6	母公司报表	        该公司母公司的财务报表数据
        7	母公司单季表	        母公司的单季度表
        8	母公司调整单季表	    母公司调整后的单季表
        9	母公司调整表	        该公司母公司的本年度公布上年同期的财务报表数据
        10	母公司调整前报表	    母公司调整之前的原始财务报表数据
        11	调整前合并报表	        调整之前合并报表原数据
        12	母公司调整前报表	    母公司报表发生变更前保留的原数据
    example:
        cashflow(ts_code='600000.SH',
                 start_date='20180101',
                 end_date='20180730',
                 fields = 'fa_fnc_leases, end_bal_cash, beg_bal_cash')
    """
    if fields is None: fields = 'ts_code,rpt_date,net_profit,finan_exp,end_bal_cash,beg_bal_cash'
    pro = ts.pro_api()
    return pro.cashflow(ts_code=ts_code,
                        ann_date=rpt_date,
                        start_date=start,
                        end_date=end,
                        period=period,
                        report_type=report_type,
                        comp_type=comp_type,
                        fields=fields)


def indicators(ts_code: str,
               rpt_date: str = None,
               start: str = None,
               end: str = None,
               period: str = None,
               fields: str = None) -> pd.DataFrame:
    """ 获取上市公司财务数据——财务指标

    :param ts_code: str, TS股票代码,e.g. 600001.SH/000001.SZ
    :param rpt_date: str, 公告日期
    :param start: str, 报告期开始日期
    :param end: str, 报告期结束日期
    :param period: str, 报告期(每个季度最后一天的日期,比如20171231表示年报)
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column                      type    default description
        ts_code				        str	    Y	TS代码
        ann_date			        str	    Y	公告日期
        end_date			        str	    Y	报告期
        eps				            float	Y	基本每股收益
        dt_eps				        float	Y	稀释每股收益
        total_revenue_ps		    float	Y	每股营业总收入
        revenue_ps			        float	Y	每股营业收入
        capital_rese_ps			    float	Y	每股资本公积
        surplus_rese_ps			    float	Y	每股盈余公积
        undist_profit_ps		    float	Y	每股未分配利润
        extra_item			        float	Y	非经常性损益
        profit_dedt			        float	Y	扣除非经常性损益后的净利润
        gross_margin			    float	Y	毛利
        current_ratio			    float	Y	流动比率
        quick_ratio			        float	Y	速动比率
        cash_ratio			        float	Y	保守速动比率
        invturn_days			    float	N	存货周转天数
        arturn_days			        float	N	应收账款周转天数
        inv_turn			        float	N	存货周转率
        ar_turn				        float	Y	应收账款周转率
        ca_turn				        float	Y	流动资产周转率
        fa_turn				        float	Y	固定资产周转率
        assets_turn			        float	Y	总资产周转率
        op_income			        float	Y	经营活动净收益
        valuechange_income		    float	N	价值变动净收益
        interst_income			    float	N	利息费用
        daa				            float	N	折旧与摊销
        ebit				        float	Y	息税前利润
        ebitda				        float	Y	息税折旧摊销前利润
        fcff				        float	Y	企业自由现金流量
        fcfe				        float	Y	股权自由现金流量
        current_exint			    float	Y	无息流动负债
        noncurrent_exint		    float	Y	无息非流动负债
        interestdebt			    float	Y	带息债务
        netdebt				        float	Y	净债务
        tangible_asset			    float	Y	有形资产
        working_capital			    float	Y	营运资金
        networking_capital		    float	Y	营运流动资本
        invest_capital			    float	Y	全部投入资本
        retained_earnings		    float	Y	留存收益
        diluted2_eps			    float	Y	期末摊薄每股收益
        bps				            float	Y	每股净资产
        ocfps				        float	Y	每股经营活动产生的现金流量净额
        retainedps			        float	Y	每股留存收益
        cfps				        float	Y	每股现金流量净额
        ebit_ps				        float	Y	每股息税前利润
        fcff_ps				        float	Y	每股企业自由现金流量
        fcfe_ps				        float	Y	每股股东自由现金流量
        netprofit_margin		    float	Y	销售净利率
        grossprofit_margin		    float	Y	销售毛利率
        cogs_of_sales			    float	Y	销售成本率
        expense_of_sales		    float	Y	销售期间费用率
        profit_to_gr			    float	Y	净利润/营业总收入
        saleexp_to_gr			    float	Y	销售费用/营业总收入
        adminexp_of_gr			    float	Y	管理费用/营业总收入
        finaexp_of_gr			    float	Y	财务费用/营业总收入
        impai_ttm			        float	Y	资产减值损失/营业总收入
        gc_of_gr			        float	Y	营业总成本/营业总收入
        op_of_gr			        float	Y	营业利润/营业总收入
        ebit_of_gr			        float	Y	息税前利润/营业总收入
        roe				            float	Y	净资产收益率
        roe_waa				        float	Y	加权平均净资产收益率
        roe_dt				        float	Y	净资产收益率(扣除非经常损益)
        roa				            float	Y	总资产报酬率
        npta				        float	Y	总资产净利润
        roic				        float	Y	投入资本回报率
        roe_yearly			        float	Y	年化净资产收益率
        roa2_yearly			        float	Y	年化总资产报酬率
        roe_avg				        float	N	平均净资产收益率(增发条件)
        opincome_of_ebt			    float	N	经营活动净收益/利润总额
        investincome_of_ebt		    float	N	价值变动净收益/利润总额
        n_op_profit_of_ebt		    float	N	营业外收支净额/利润总额
        tax_to_ebt			        float	N	所得税/利润总额
        dtprofit_to_profit		    float	N	扣除非经常损益后的净利润/净利润
        salescash_to_or			    float	N	销售商品提供劳务收到的现金/营业收入
        ocf_to_or			        float	N	经营活动产生的现金流量净额/营业收入
        ocf_to_opincome			    float	N	经营活动产生的现金流量净额/经营活动净收益
        capitalized_to_da		    float	N	资本支出/折旧和摊销
        debt_to_assets			    float	Y	资产负债率
        assets_to_eqt			    float	Y	权益乘数
        dp_assets_to_eqt		    float	Y	权益乘数(杜邦分析)
        ca_to_assets			    float	Y	流动资产/总资产
        nca_to_assets			    float	Y	非流动资产/总资产
        tbassets_to_totalassets		float	Y	有形资产/总资产
        int_to_talcap			    float	Y	带息债务/全部投入资本
        eqt_to_talcapital		    float	Y	归属于母公司的股东权益/全部投入资本
        currentdebt_to_debt		    float	Y	流动负债/负债合计
        longdeb_to_debt			    float	Y	非流动负债/负债合计
        ocf_to_shortdebt		    float	Y	经营活动产生的现金流量净额/流动负债
        debt_to_eqt			        float	Y	产权比率
        eqt_to_debt			        float	Y	归属于母公司的股东权益/负债合计
        eqt_to_interestdebt		    float	Y	归属于母公司的股东权益/带息债务
        tangibleasset_to_debt		float	Y	有形资产/负债合计
        tangasset_to_intdebt		float	Y	有形资产/带息债务
        tangibleasset_to_netdebt	float	Y	有形资产/净债务
        ocf_to_debt			        float	Y	经营活动产生的现金流量净额/负债合计
        ocf_to_interestdebt		    float	N	经营活动产生的现金流量净额/带息债务
        ocf_to_netdebt			    float	N	经营活动产生的现金流量净额/净债务
        ebit_to_interest		    float	N	已获利息倍数(EBIT/利息费用)
        longdebt_to_workingcapital	float	N	长期债务与营运资金比率
        ebitda_to_debt			    float	N	息税折旧摊销前利润/负债合计
        turn_days			        float	Y	营业周期
        roa_yearly			        float	Y	年化总资产净利率
        roa_dp				        float	Y	总资产净利率(杜邦分析)
        fixed_assets			    float	Y	固定资产合计
        profit_prefin_exp		    float	N	扣除财务费用前营业利润
        non_op_profit			    float	N	非营业利润
        op_to_ebt			        float	N	营业利润／利润总额
        nop_to_ebt			        float	N	非营业利润／利润总额
        ocf_to_profit			    float	N	经营活动产生的现金流量净额／营业利润
        cash_to_liqdebt			    float	N	货币资金／流动负债
        cash_to_liqdebt_withinterest	float	N	货币资金／带息流动负债
        op_to_liqdebt			    float	N	营业利润／流动负债
        op_to_debt			        float	N	营业利润／负债合计
        roic_yearly			        float	N	年化投入资本回报率
        total_fa_trun			    float	N	固定资产合计周转率
        profit_to_op			    float	Y	利润总额／营业收入
        q_opincome			        float	N	经营活动单季度净收益
        q_investincome			    float	N	价值变动单季度净收益
        q_dtprofit			        float	N	扣除非经常损益后的单季度净利润
        q_eps				        float	N	每股收益(单季度)
        q_netprofit_margin		    float	N	销售净利率(单季度)
        q_gsprofit_margin		    float	N	销售毛利率(单季度)
        q_exp_to_sales			    float	N	销售期间费用率(单季度)
        q_profit_to_gr			    float	N	净利润／营业总收入(单季度)
        q_saleexp_to_gr			    float	Y	销售费用／营业总收入 (单季度)
        q_adminexp_to_gr		    float	N	管理费用／营业总收入 (单季度)
        q_finaexp_to_gr			    float	N	财务费用／营业总收入 (单季度)
        q_impair_to_gr_ttm		    float	N	资产减值损失／营业总收入(单季度)
        q_gc_to_gr			        float	Y	营业总成本／营业总收入 (单季度)
        q_op_to_gr			        float	N	营业利润／营业总收入(单季度)
        q_roe				        float	Y	净资产收益率(单季度)
        q_dt_roe			        float	Y	净资产单季度收益率(扣除非经常损益)
        q_npta				        float	Y	总资产净利润(单季度)
        q_opincome_to_ebt		    float	N	经营活动净收益／利润总额(单季度)
        q_investincome_to_ebt		float	N	价值变动净收益／利润总额(单季度)
        q_dtprofit_to_profit		float	N	扣除非经常损益后的净利润／净利润(单季度)
        q_salescash_to_or		    float	N	销售商品提供劳务收到的现金／营业收入(单季度)
        q_ocf_to_sales			    float	Y	经营活动产生的现金流量净额／营业收入(单季度)
        q_ocf_to_or			        float	N	经营活动产生的现金流量净额／经营活动净收益(单季度)
        basic_eps_yoy			    float	Y	基本每股收益同比增长率(%)
        dt_eps_yoy			        float	Y	稀释每股收益同比增长率(%)
        cfps_yoy			        float	Y	每股经营活动产生的现金流量净额同比增长率(%)
        op_yoy				        float	Y	营业利润同比增长率(%)
        ebt_yoy				        float	Y	利润总额同比增长率(%)
        netprofit_yoy			    float	Y	归属母公司股东的净利润同比增长率(%)
        dt_netprofit_yoy		    float	Y	归属母公司股东的净利润-扣除非经常损益同比增长率(%)
        ocf_yoy				        float	Y	经营活动产生的现金流量净额同比增长率(%)
        roe_yoy				        float	Y	净资产收益率(摊薄)同比增长率(%)
        bps_yoy				        float	Y	每股净资产相对年初增长率(%)
        assets_yoy			        float	Y	资产总计相对年初增长率(%)
        eqt_yoy				        float	Y	归属母公司的股东权益相对年初增长率(%)
        tr_yoy				        float	Y	营业总收入同比增长率(%)
        or_yoy				        float	Y	营业收入同比增长率(%)
        q_gr_yoy			        float	N	营业总收入同比增长率(%)(单季度)
        q_gr_qoq			        float	N	营业总收入环比增长率(%)(单季度)
        q_sales_yoy			        float	Y	营业收入同比增长率(%)(单季度)
        q_sales_qoq			        float	N	营业收入环比增长率(%)(单季度)
        q_op_yoy			        float	N	营业利润同比增长率(%)(单季度)
        q_op_qoq			        float	Y	营业利润环比增长率(%)(单季度)
        q_profit_yoy		    	float	N	净利润同比增长率(%)(单季度)
        q_profit_qoq			    float	N	净利润环比增长率(%)(单季度)
        q_netprofit_yoy			    float	N	归属母公司股东的净利润同比增长率(%)(单季度)
        q_netprofit_qoq			    float	N	归属母公司股东的净利润环比增长率(%)(单季度)
        equity_yoy			        float	Y	净资产同比增长率
        rd_exp				        float	N	研发费用
        update_flag			        str	    N	更新标识
    example:
        indicator(ts_code='600000.SH', fields = 'ts_code,ann_date,eps,dt_eps,total_revenue_ps,revenue_ps')
    output:
              ts_code  ann_date    eps  dt_eps  total_revenue_ps  revenue_ps
        0   600000.SH  20191030  1.620    1.62            4.9873      4.9873
        1   600000.SH  20190824  1.070    1.07            3.3251      3.3251
        2   600000.SH  20190430  0.530    0.53            1.7063      1.7063
        3   600000.SH  20190326  1.850    1.85            5.8443      5.8443
        4   600000.SH  20181031  1.440    1.44            4.3305      4.3305
    """
    if fields is None: fields = 'ts_code,ann_date,eps,dt_eps,total_revenue_ps,revenue_ps'
    pro = ts.pro_api()
    return pro.fina_indicator(ts_code=ts_code,
                              ann_date=rpt_date,
                              start_date=start,
                              end_date=end,
                              period=period,
                              fields=fields)


# Market Data
# =================

def top_list(trade_date: str = None,
             ts_code: str = None,
             fields: str = None) -> pd.DataFrame:
    """ 龙虎榜每日交易明细，2005年至今全部历史数据，单次获取数量不超过10000

    :param trade_date: str, 交易日期
    :param ts_code: str, 股票代码
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column                      type    default description
        trade_date	                str	    Y	    交易日期
        ts_code		                str	    Y	    TS代码
        name		                str	    Y	    名称
        close		                float	Y	    收盘价
        pct_change	                float	Y	    涨跌幅
        turnover_rate	            float	Y	    换手率
        amount		                float	Y	    总成交额
        l_sell		                float	Y	    龙虎榜卖出额
        l_buy		                float	Y	    龙虎榜买入额
        l_amount	                float	Y	    龙虎榜成交额
        net_amount	                float	Y	    龙虎榜净买入额
        net_rate	                float	Y	    龙虎榜净买额占比
        amount_rate	                float	Y	    龙虎榜成交额占比
        float_values	            float	Y	    当日流通市值
        reason		                str	    Y	    上榜理由
    example:
        top_list(trade_date='20180928', fields='trade_date,ts_code,name,close')
    output:
           trade_date    ts_code  name   close
        0    20180928  000007.SZ   全新好   7.830
        1    20180928  000017.SZ  深中华A   4.660
        2    20180928  000505.SZ  京粮控股   5.750
        3    20180928  000566.SZ  海南海药   6.120
        4    20180928  000593.SZ  大通燃气   7.990
        ...
    """
    if fields is None: fields = 'trade_date,ts_code,name,close,l_sell,l_buy,l_amount,net_amount,net_rate,amount_rate'
    pro = ts.pro_api()
    return pro.top_list(trade_date=trade_date,
                        ts_code=ts_code,
                        fields=fields)


# Index Data
# ==================

def index_basic(trade_date: str = None,
                ts_code: str = None,
                start: str = None,
                end: str = None,
                fields: str = None) -> pd.DataFrame:
    """ 大盘指数每日指标, 目前只提供上证综指，深证成指，上证50，中证500，中小板指，创业板指的每日指标数据

    :param trade_date: str, 交易日期 （格式：YYYYMMDD，比如20181018，下同）
    :param ts_code: str, TS代码
    :param start: str, 开始日期
    :param end: str, 结束日期
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return:
        column          type    default description
        ts_code		    str	    Y	    TS代码
        trade_date	    str	    Y	    交易日期
        total_mv	    float	Y	    当日总市值（元）
        float_mv	    float	Y	    当日流通市值（元）
        total_share     float	Y	    当日总股本（股）
        float_share	    float	Y	    当日流通股本（股）
        free_share	    float	Y	    当日自由流通股本（股）
        turnover_rate	float	Y	    换手率
        turnover_rate_f	float	Y	    换手率(基于自由流通股本)
        pe		        float	Y	    市盈率
        pe_ttm		    float	Y	    市盈率TTM
        pb		        float	Y	    市净率
    example:
        index_basic(trade_date='20181018', fields='ts_code,trade_date,turnover_rate,pe')
    output:
            ts_code  trade_date  turnover_rate     pe
        0  000001.SH   20181018           0.38  11.92
        1  000300.SH   20181018           0.27  11.17
        2  000905.SH   20181018           0.82  18.03
        3  399001.SZ   20181018           0.88  17.48
        4  399005.SZ   20181018           0.85  21.43
        5  399006.SZ   20181018           1.50  29.56
        6  399016.SZ   20181018           1.06  18.86
        7  399300.SZ   20181018           0.27  11.17
    """
    pro = ts.pro_api()
    return pro.index_dailybasic(trade_date=trade_date,
                                ts_code=ts_code,
                                start_date=start,
                                end_date=end,
                                fields=fields)


def composite(index_code: str = None,
              trade_date: str = None,
              start: str = None,
              end: str = None) -> pd.DataFrame:
    """ 获取各类指数成分和权重，月度数据 ，如需日度指数成分和权重，请联系 waditu@163.com

    :param index_code: str, 指数代码 (二选一)
    :param trade_date: str, 交易日期 （二选一）
    :param start: str, 开始日期
    :param end: str, 结束日期
    :return: pd.DataFrame
        column      type    description
        index_code	str	    指数代码
        con_code	str	    成分代码
        trade_date	str	    交易日期
        weight	 	float	权重
    example:
        composite(index_code='399300.SZ', start_date='20180901', end_date='20180930')
    output:
            index_code   con_code trade_date  weight
        0    399300.SZ  000001.SZ   20180903  0.8656
        1    399300.SZ  000002.SZ   20180903  1.1330
        2    399300.SZ  000060.SZ   20180903  0.1125
        3    399300.SZ  000063.SZ   20180903  0.4273
        4    399300.SZ  000069.SZ   20180903  0.2010
        5    399300.SZ  000157.SZ   20180903  0.1699
        6    399300.SZ  000402.SZ   20180903  0.0816
    """
    pro = ts.pro_api()
    return pro.index_weight(index_code=index_code,
                            trade_date=trade_date,
                            start_date=start,
                            end_date=end)


# Funds Data
# ==============


def fund_net_value(ts_code: str = None,
                   date: str = None,
                   market: str = None,
                   fields: str = None) -> pd.DataFrame:
    """ 获取公募基金净值数据

    :param ts_code: str, TS基金代码 （二选一）如果可用，给出该基金的历史净值记录
    :param trade_date: str, 净值日期 （二选一）如果可用，给出该日期所有基金的净值记录
    :param market: str, 交易市场类型: E场内 O场外
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column          type  default   description
        ts_code		    str	    Y	    TS代码
        ann_date	    str	    Y      	公告日期
        end_date	    str	    Y	    截止日期
        unit_nav	    float	Y	    单位净值
        accum_nav	    float	Y	    累计净值
        accum_div	    float	Y   	累计分红
        net_asset	    float	Y   	资产净值
        total_netasset	float	Y   	合计资产净值
        adj_nav		    float	Y   	复权单位净值
    example:
        fund_neg_value(ts_code='165509.SZ', fields='ts_code, adj_nav')
    output:
        ts_code   adj_nav
        0     165509.SZ  1.827306
        1     165509.SZ  1.811019
        2     165509.SZ  1.815905
        3     165509.SZ  1.801248
        4     165509.SZ  1.835449
        ...         ...       ...
    """
    pro = ts.pro_api()
    return pro.fund_nav(ts_code=ts_code,
                        end_date=date,
                        market=market,
                        fields=fields)


# Futures & Options Data
# ===============


def future_basic(exchange: str = None,
                 future_type: str = None,
                 fields: str = None) -> pd.DataFrame:
    """ 获取期货合约列表数据

    :param exchange: str, 交易所代码 CFFEX-中金所 DCE-大商所 CZCE-郑商所 SHFE-上期所 INE-上海国际能源交易中心
    :param future_type: str, 合约类型 (1 普通合约 2主力与连续合约 默认取全部)
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return:
        column          type    default description
        ts_code		    str	    Y	    合约代码
        symbol		    str	    Y	    交易标识
        exchange	    str	    Y	    交易市场
        name		    str	    Y	    中文简称
        fut_code	    str	    Y	    合约产品代码
        multiplier	    float	Y	    合约乘数
        trade_unit	    str	    Y	    交易计量单位
        per_unit	    float	Y	    交易单位(每手)
        quote_unit	    str	    Y	    报价单位
        quote_unit_desc	str	    Y	    最小报价单位说明
        d_mode_desc	    str	    Y	    交割方式说明
        list_date	    str	    Y	    上市日期
        delist_date	    str	    Y	    最后交易日期
        d_month		    str	    Y	    交割月份
        last_ddate	    str	    Y	    最后交割日
        trade_time_desc	str	    N	    交易时间说明
    example:
        future_basic(exchange='DCE', fut_type='1', fields='ts_code,symbol,name,list_date,delist_date')
    output:
                ts_code  symbol      name   list_date    delist_date
        0      P0805.DCE   P0805   棕榈油0805  20071029    20080516
        1      P0806.DCE   P0806   棕榈油0806  20071029    20080616
        2      P0807.DCE   P0807   棕榈油0807  20071029    20080714
        3      P0808.DCE   P0808   棕榈油0808  20071029    20080814
        4      P0811.DCE   P0811   棕榈油0811  20071115    20081114
        5      P0812.DCE   P0812   棕榈油0812  20071217    20081212
        ...
    """
    pro = ts.pro_api()
    return pro.fut_basic(exchange=exchange,
                         fut_type=future_type,
                         fields=fields)


def options_basic(exchange: str = None,
                  option_type: str = None,
                  fields: str = None) -> pd.DataFrame:
    """ 获取期权合约信息

    :param exchange: str, 交易所代码 CFFEX-中金所 DCE-大商所 CZCE-郑商所 SHFE-上期所 INE-上海国际能源交易中心
    :param option_type: str, 期权类型 (??)
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return pd.DataFrame
        column          type    default description
        ts_code		    str	    Y   	TS代码
        exchange	    str 	Y   	交易市场
        name		    str 	Y   	合约名称
        per_unit	    str 	Y   	合约单位
        opt_code    	str 	Y   	标准合约代码
        opt_type    	str 	Y   	合约类型
        call_put    	str 	Y   	期权类型
        exercise_type	str 	Y   	行权方式
        exercise_price	float	Y   	行权价格
        s_month	    	str	    Y   	结算月
        maturity_date	str 	Y   	到期日
        list_price  	float	Y   	挂牌基准价
        list_date   	str 	Y   	开始交易日期
        delist_date 	str 	Y   	最后交易日期
        last_edate  	str 	Y   	最后行权日期
        last_ddate  	str 	Y   	最后交割日期
        quote_unit  	str 	Y   	报价单位
        min_price_chg	str 	Y   	最小价格波幅
    example:
        options_basic(exchange='DCE', fields='ts_code,name,exercise_type,list_date,delist_date')
    output:
                    ts_code                  name             exercise_type list_date delist_date
        0    M1707-C-2400.DCE  豆粕期权1707认购2400            美式  20170605    20170607
        1    M1707-P-2400.DCE  豆粕期权1707认沽2400            美式  20170605    20170607
        2    M1803-P-2550.DCE  豆粕期权1803认沽2550            美式  20170407    20180207
        3    M1707-C-2500.DCE  豆粕期权1707认购2500            美式  20170410    20170607
        4    M1707-P-2500.DCE  豆粕期权1707认沽2500            美式  20170410    20170607
        5    M1803-C-2550.DCE  豆粕期权1803认购2550            美式  20170407    20180207
    """
    pro = ts.pro_api()
    return pro.opt_basic(exchange=exchange,
                         call_put=option_type,
                         fields=fields)


def future_daily(trade_date: str = None,
                 ts_code: str = None,
                 exchange: str = None,
                 start: str = None,
                 end: str = None,
                 fields: str = None) -> pd.DataFrame:
    """ 期货日线行情数据

    :param trade_date: str, 交易日期
    :param ts_code: str, 合约代码
    :param exchange: str, 交易所代码
    :param start: str, 开始日期
    :param end: str, 结束日期
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column      type    default description
        ts_code		str	    Y	    TS合约代码
        trade_date	str	    Y	    交易日期
        pre_close	float	Y	    昨收盘价
        pre_settle	float	Y   	昨结算价
        open		loat	Y	    开盘价
        high		float	Y   	最高价
        low		    float	Y	    最低价
        close		float	Y	    收盘价
        settle		float	Y	    结算价
        change1		float	Y   	涨跌1 收盘价-昨结算价
        change2		float	Y   	涨跌2 结算价-昨结算价
        vol		    float	Y   	成交量(手)
        amount		float	Y   	成交金额(万元)
        oi		    float	Y   	持仓量(手)
        oi_chg		float	Y   	持仓量变化
        delv_settle	float	N   	交割结算价
    example:
        future_daily(ts_code='CU1811.SHF', start_date='20180101', end_date='20181113')
    output:
                ts_code trade_date  pre_close  pre_settle     open   ...  change2      vol     amount       oi  oi_chg
        0    CU1811.SHF   20181113    48900.0     49030.0  48910.0   ...   -200.0  17270.0  421721.70  16110.0 -6830.0
        1    CU1811.SHF   20181112    49270.0     49340.0  49130.0   ...   -310.0  27710.0  679447.85  22940.0 -7160.0
        2    CU1811.SHF   20181109    49440.0     49500.0  49340.0   ...   -160.0  22530.0  555910.15  30100.0 -4700.0
        3    CU1811.SHF   20181108    49470.0     49460.0  49600.0   ...     40.0  22290.0  551708.00  34800.0 -3530.0
        4    CU1811.SHF   20181107    49670.0     49630.0  49640.0   ...   -170.0  26850.0  664040.10  38330.0 -4560.0
        ..          ...        ...        ...         ...      ...   ...      ...      ...        ...      ...     ...
    """
    pro = ts.pro_api()
    return pro.fut_daily(trade_date=trade_date,
                         ts_code=ts_code,
                         exchange=exchange,
                         start_date=start,
                         end_date=end,
                         fields=fields)


def options_daily(trade_date: str = None,
                  ts_code: str = None,
                  exchange: str = None,
                  start: str = None,
                  end: str = None,
                  fields: str = None) -> pd.DataFrame:
    """ 获取期权日线行情

    :param trade_date: str, 交易日期
    :param ts_code: str, 合约代码
    :param exchange: str, 交易所代码
    :param start: str, 开始日期
    :param end: str, 结束日期
    :param fields: str, 输出数据字段，结果DataFrame的数据列名，用逗号分隔
    :return: pd.DataFrame
        column      type    default description
        ts_code		str	    Y   	TS代码
        trade_date	str	    Y   	交易日期
        exchange	str	    Y   	交易市场
        pre_settle	float	Y   	昨结算价
        pre_close	float	Y   	前收盘价
        open		float	Y   	开盘价
        high		float	Y   	最高价
        low		    float	Y   	最低价
        close		float	Y   	收盘价
        settle		float	Y   	结算价
        vol		    float	Y   	成交量(手)
        amount		float	Y   	成交金额(万元)
        oi		    float	Y   	持仓量(手)
    example:
        options_daily(trade_date='20181212')
    output:
                  ts_code      trade_date exchange  pre_settle  pre_close     open  \
        0         10001313.SH   20181212      SSE      0.0311     0.0312    0.0355
        1         10001314.SH   20181212      SSE      0.0156     0.0157    0.0170
        2         10001315.SH   20181212      SSE      0.0073     0.0073    0.0076
        3         10001316.SH   20181212      SSE      0.0028     0.0028    0.0029
        4         10001317.SH   20181212      SSE      0.0015     0.0015    0.0015
        5         10001318.SH   20181212      SSE      0.0009     0.0009    0.0009

                 high       low     close    settle     vol       amount       oi
        0      0.0368    0.0293    0.0309    0.0307  3.8354  12614354.72  98882.0
        1      0.0190    0.0142    0.0150    0.0150  1.4472   2349332.88  79980.0
        2      0.0085    0.0060    0.0062    0.0062  1.0092    693117.76  72370.0
        3      0.0042    0.0024    0.0027    0.0027  0.5434    161072.24  55117.0
        4      0.0018    0.0012    0.0013    0.0013  0.4240     57989.19  61746.0
        5      0.0012    0.0008    0.0008    0.0008  0.2067     20700.88  37674.0
    """
    pro = ts.pro_api()
    return pro.opt_daily(trade_date=trade_date,
                         ts_code=ts_code,
                         exchange=exchange,
                         start_date=start,
                         end_date=end,
                         fields=fields)


# TODO: 将History类改为MySQL数据库模块，管理本地历史数据
class History:
    '历史数据管理类，使用一个“历史数据仓库 Historical Warehouse”来管理所有的历史数据'
    '''使用tushare包来下载各种历史数据，将所有历史数据打包存储为历史数据仓库格式，在需要使用的时候
    从仓库中读取数据并确保数据格式的统一。统一的数据格式为Universal Historical Format'''
    # 类属性：
    # 数据仓库存储文件夹（未来可以考虑使用某种数据库格式来存储所有的历史数据）
    __warehouse_dir = 'qteasy/history/'
    # 不同类型的数据
    __intervals = {'d': 'daily', 'w': 'weekly', '30': '30min', '15': '15min'}

    PRICE_TYPES = ['close',
                   'open',
                   'high',
                   'low',
                   'volume',
                   'value']

    def __init__(self):
        # 可用的历史数据通过extract方法存储到extract属性中
        # 所有数据通过整理后存储在数据仓库中 warehouse
        # 在磁盘上可以同时保存多个不同的数据仓库，数据仓库必须打开后才能导出数据，同时只能打开一个数据仓库 
        # 每个数据仓库就是一张数据表，包含所有股票在一定历史时期内的一种特定的数据类型，如5分钟开盘价
        # 以上描述为第一个版本的数据组织方式，以后可以考虑采用数据库来组织数据
        # 对象属性：

        self.days_work = [1, 2, 3, 4, 5]  # 每周工作日
        self.__warehouse = pd.DataFrame()  # 打开的warehouse
        self.__open_wh_file = ''  #
        self.__open_price_type = ''
        self.__open_interval = ''
        self.__open_wh_shares = set()
        self.__warehouse_is_open = False
        self.__extract = pd.DataFrame()
        self.__extracted = False

        # =========================
        # set up tushare token and account
        # =========================
        token = '14f96621db7a937c954b1943a579f52c09bbd5022ed3f03510b77369'
        self.ts_pro = ts.pro_api(token)

    # 以下为只读对象属性
    @property
    def wh_path(self):  # 当前打开的仓库的路径和文件名
        return self.__open_wh_file

    @property
    def wh_is_open(self):  # 当有仓库文件打开时返回True
        return self.__warehouse_is_open

    @property
    def price_type(self):  # 当前打开的仓库文件的数据类型
        return self.__open_price_type

    @property
    def freq(self):  # 当前打开的仓库文件的数据间隔
        return self.__open_interval

    @property
    def wh_shares(self):  # 当前打开的仓库文件包含的股票
        return self.__open_wh_shares

    @property
    def warehouse(self):  # 返回当前打开的数据仓库
        return self.__warehouse

    @property
    def hist_list(self):  # 返回当前提取出来的数据表
        return self.__extract

    # 对象方法：
    def hist_list(self, shares=None, start=None, end=None, freq=None):
        # 提取一张新的数据表
        raise NotImplementedError

    def info(self):
        # 打印当前数据仓库的关键信息
        if self.__warehouse_is_open:
            print('warehouse is open: ')
            print('warehouse path: ', self.__open_wh_file)
            print('price type: ', self.__open_price_type, 'time freq:', self.__open_interval)
            print('warehouse info: ')
            print(self.__warehouse.info())
        else:
            print('No warehouse history')

    def read_warehouse(self, price_type='close', interval='d'):
        # 从磁盘上读取数据仓库
        # 输入：
        # price_type： 数据类型
        # interval： 数据间隔
        # 输出：=====
        # data： 读取的数据（DataFrame对象）
        # fname：所读取的文件名
        # intervals = {'d': 'daily', 'w': 'weekly', '30': '30min', '15': '15min'}
        fname = self.__warehouse_dir + '_share_' + self.__intervals[interval] + '_' + price_type + '.csv'
        data = pd.read_csv(fname, index_col='date')
        data.index = pd.to_datetime(data.index, format='%Y-%m-%d')
        return data, fname

    def warehouse_new(self, code, price_type, hist_data):
        # 读取磁盘上现有的数据，并生成一个数据仓库
        raise NotImplementedError

    def warehouse_open(self, price_type='close', interval='d'):
        # 打开一个新的数据仓库，关闭并存储之前打开的那一个
        if self.__open_price_type != price_type or self.__open_interval != interval:
            data, fname = self.read_warehouse(price_type, interval)
            self.__warehouse = data
            self.__open_wh_file = fname
            self.__open_price_type = price_type
            self.__open_interval = interval
            self.__open_wh_shares = set(self.__warehouse.columns)
            self.__warehouse_is_open = True

    def warehouse_update(self, codes, interval):
        # 读取最新的历史数据并更新已读取的数据仓库文件添加新增的数据
        # basics = pd.read_csv('qteasy/__share_basics.csv', index_col='code')
        # print basics.head()
        code_set = self.__make_share_set(codes)
        # print 'code set', code_set, 'len', len(code_set)
        # print code_set.issubset(set(basics.index))
        # if code_set.issubset(set(basics.index)) and len(code_set) > 0:
        if len(code_set) > 0:
            print('loading warehouses...')
            wh_close, f1 = self.read_warehouse('close', interval)
            wh_open, f2 = self.read_warehouse('open', interval)
            wh_high, f3 = self.read_warehouse('high', interval)
            wh_low, f4 = self.read_warehouse('low', interval)
            wh_vol, f5 = self.read_warehouse('volume', interval)
            wh_dict = {'close': wh_close, 'open': wh_open, 'high': wh_high,
                       'low': wh_low, 'volume': wh_vol}
            # update the shape of all wharehouses by merging new columns or new rows
            # and then update
            print('generating expanding dataframe...')
            last_day = wh_close.index[-1].date()
            codes_in_wh = set(wh_close.columns)
            new_code_set = code_set.difference(codes_in_wh)
            # create the expanding df that contains extended rows and columns
            days = self.trade_days(start=last_day, freq=interval)
            # print days
            index = pd.Index(days, name='date')
            expand_df = pd.DataFrame(index=index, columns=new_code_set)
            # print 'expand_df:', expand_df
            # merge all temp wh one by one
            # in order to update the warehouse, the size of dataframe should be modified
            if len(expand_df.index) > 0 or len(expand_df.columns) > 0:
                # if not expand_df.empty:
                print('df merged')
                for tp in ['close', 'open', 'high', 'low', 'volume']:
                    wh_dict[tp] = pd.merge(wh_dict[tp], expand_df, left_index=True,
                                           right_index=True, how='outer')
            # print 'warehouse merged: ', wh_dict['close'].index
            # read data and update all warehouses
            # print 'code_set:', code_set
            print('reading tushare data and updating warehouse...')
            count = 0
            for code in code_set:
                count += 1
                try:
                    data = self.get_new_price(code, interval)
                    # print data
                    msg = 'reading data ' + str(code) + ', progress: ' + str(count) + ' of ' + str(len(code_set))
                    print(msg, end='\r')
                    for tp in ['close', 'open', 'high', 'low', 'volume']:
                        # in order to update the warehouse, the size of dataframe should be modified
                        df = pd.DataFrame(data[tp])
                        df.columns = [code]
                        # print df.tail()
                        # print wh_dict[tp].tail().loc[:][code]
                        wh_dict[tp].update(df)
                        # print 'dataFrame updated: ', wh_dict[tp][code].tail()
                except:
                    print('data cannot be read:', code, 'resume next,', count, 'of', len(code_set))
                    # save all updated warehouses
            print('\n', 'data updated, saving warehouses...')
            for tp in ['close', 'open', 'high', 'low', 'volume']:
                # in order to update the warehouse, the size of dataframe should be modified
                fname = self.__warehouse_dir + '_share_' + self.__intervals[interval] + '_' + tp + '.csv'
                wh_dict[tp].to_csv(fname)
            return True

    def warehouse_save(self):
        # 保存但不关闭数据仓库
        self.__warehouse.to_csv(self.__open_wh_file)
        pass

    def warehouse_close(self):
        # 关闭但不保存数据仓库
        if self.__warehouse_is_open:
            self.__warehouse = pd.DataFrame()
            self.__open_wh_file = ''
            self.__open_price_type = ''
            self.__open_interval = ''
            self.__open_wh_shares = set()
            self.__warehouse_is_open = False
        else:
            print('no warehouse opened')
        return self.__warehouse_is_open

    def warehouse_extract(self, shares, start, end):
        # 从打开的数据仓库中提取数据
        share_set = self.__make_share_set(shares)
        if share_set.issubset(self.__open_wh_shares):
            try:
                start = pd.to_datetime(start)
                end = pd.to_datetime(end)
                data = self.__warehouse.loc[start:end][shares]
                self.__extracted = True
                self.__extract = data
            except:
                print('Data Not extracted: date format should be %Y-%m-%d!')
                self.remove_extract()
        else:
            print('Data NOT extracted: one or more share(s) is not in the warehouse, check your input')
            self.remove_extract()
        return self.__extract

    def warehouse_get_last(self, code):
        # 从打开的数据仓库中提取指定股票的最后的数据及日期
        if self.__warehouse_is_open:
            if code in self.__warehouse.columns:
                data = self.__warehouse
                # print data.head()
                col = code
                # print col
                record = data[col]
                # print record.tail()
                if len(record) > 0:
                    date = record.last_valid_index()
                    price = record[date]
                else:
                    date = datetime.today() + dt.timedelta(-1077)
                    price = 0.0
                return date, price
            else:
                return dt.date(2018, 1, 1), 0.0

    def get_new_price(self, code, interval='d'):
        # 使用tushare读取某只股票的最新数据，指定数据间隔
        # print 'running get_new_price'
        if self.__open_price_type != 'close' and self.__open_interval != interval:
            self.warehouse_open(price_type='close', interval=interval)
        pre_date, pre_close = self.warehouse_get_last(code=code)
        # print pre_date, pre_close
        start = (pre_date + dt.timedelta(1)).strftime('%Y-%m-%d')
        # print code, start, interval
        data = ts.get_hist_data(code, start=start, ktype=interval)
        data = data[::-1][['open', 'close', 'low', 'high', 'volume', 'price_change']]
        # print data.head()
        if pre_close == 0.0:
            pre_close = data.iloc[0].close
        data['price_close'] = data.price_change.cumsum() + pre_close
        data['diff'] = data.price_close - data.close
        # print data.head()
        for tp in ['open', 'high', 'low']:
            data[tp] = np.round(data[tp] + data['diff'], 2)
        # print data.head()
        data.close = np.round(data.price_close, 2)
        data.index = pd.to_datetime(data.index, format='%Y-%m-%d')
        # print data.head()
        # print 'price_get completed!!'
        return data[['open', 'close', 'low', 'high', 'volume']]

    def extract(self, shares, price_type='close', start=None, end=None, interval='d'):
        # 从打开的数据仓库中提取所需的数据
        start, end = self.__check_default_dates(start, end)
        self.warehouse_open(price_type=price_type, interval=interval)
        return self.warehouse_extract(shares, start, end)

    def remove_extract(self):
        # 清空已经提取的数据表
        self.__extract = pd.DataFrame()
        self.__extracted = False

    def work_days(self, start=None, end=None, freq='d'):
        # 生成开始到结束日之间的所有工作日（根据对象属性工作日确定）
        # 公共假日没有考虑在本方法中
        start, end = self.__check_default_dates(start, end)
        w_days = []
        tag_date = start
        while tag_date < end:
            if tag_date.weekday() in self.days_work:
                w_days.append(tag_date)
            tag_date += dt.timedelta(days=1)
        return w_days

    def trade_days(self, start=None, end=None, freq='d'):
        # 生成开始日到结束日之间的所有交易日
        # 根据freq参数生成交易日序列内的交易时间点序列
        open_AM = '10:00:00'
        close_AM = '11:30:00'
        open_PM = '13:30:00'
        close_PM = '15:00:00'
        start, end = self.__check_default_dates(start, end)
        day0 = dt.date(1990, 12, 19)  # the first trade day in the trade day list
        end = (end - day0).days
        start = (start - day0).days
        trade_list = ts.trade_cal()
        trade_list = trade_list[start:end][trade_list['isOpen'] == 1]['calendarDate']
        if freq == 'd' or freq == 'D':
            return trade_list.values
        elif freq == '30' or freq == '15':
            T_list = []
            for days in trade_list.values:
                open_ = days + ' ' + open_AM
                close_ = days + ' ' + close_AM
                T_list.extend(pd.date_range(start=open_, end=close_, freq=freq + 'min').values)
                open_ = days + ' ' + open_PM
                close_ = days + ' ' + close_PM
                T_list.extend(pd.date_range(start=open_, end=close_, freq=freq + 'min').values)
            return T_list
        elif freq == 'w':
            pass
        else:
            pass

    def __check_default_dates(self, start, end):
        # 生成默认的开始和结束日（当其中一个或两者都为None时）
        if end == None:
            end = datetime.today().date()  # 如果end为None则设置end为今天
        if start == None:
            start = end + dt.timedelta(-30)  # 如果start为None则设置Start为end前30天
        return start, end

    def __make_share_set(self, shares):
        # 创建包含列表中所有股票元素的集合（去掉重复的股票）
        if type(shares) == str:
            share_set = set()
            share_set.add(shares)
        else:
            share_set = set(shares)
        return share_set
        # all_share.to_csv('qteasy/__share_basics.csv')
        # all_share.to_hdf('qteasy/__share_basics.hdf', 'key1', mode = 'w')
