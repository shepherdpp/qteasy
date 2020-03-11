# coding=utf-8

import pandas as pd
import tushare as ts
import numpy as np
from datetime import datetime
import datetime as dt


# TODO: 将History类重新定义为History模块，取消类的定义，转而使History模块变成对历史数据进行操作或读取的一个函数包的集合
# TODO: 增加HistData类，一个以Ndarray为基础的三维历史数据数组
# TODO: 需要详细定义这个函数的函数包的清单，以便其他模块调用
# TODO: 以tushare为基础定义历史数据公共函数库


class HistoryPanel():
    """The major data structure to be used for the qteasy quants system.

    data structure and class containing multiple types of array-like data framework
    axis 1: levels / share_pool
    axis 2: rows / index / hdates
    axis 3: columns / htypes
    """

    def __init__(self, values, levels=None, rows=None, columns=None):
        """

        :param values:
        :param levels:
        :param rows: datetime range or timestamp index of the data
        :param columns:
        """
        assert isinstance(values, np.ndarray), f'input value type should be numpy ndarray, got {type(value)}'
        assert len(values.shape) <= 3, \
            f'input array should be equal to or less than 3 dimensions, got {len(values.shape)}'

        if len(values.shape) == 1:
            values = values.reshape(1, 1, values.shape[0])
        elif len(values.shape) == 2:
            values = values.reshape(1, *values.shape)
        self._l_count, self._r_count, self._c_count = values.shape
        self._values = values

        if levels is None:
            levels = range(self._l_count)
        assert len(levels) == self._l_count, \
            f'length of level list does not fit the shape of input values! lenth {len(levels)} != {self._l_count}'
        self._levels = dict(zip(levels, range(self._l_count)))

        if rows is None:
            rows = range(self._r_count)
        assert len(rows) == self._r_count, \
            f'length of row list does not fit the shape of input values! lenth {len(rows)} != {self._r_count}'
        self._rows = dict(zip(rows, range(self._r_count)))

        if columns is None:
            columns = range(self._c_count)
        else:
            columns = list(map(str, columns))
            columns = list(map(str.lower, columns))
        assert len(columns) == self._c_count, \
            f'length of column list does not fit the shape of input values! lenth {len(columns)} != {self._c_count}'
        self._columns = dict(zip(columns, range(self._c_count)))

    @property
    def values(self):
        return self._values

    @property
    def levels(self):
        return self._levels

    @property
    def shares(self):
        return self._levels

    @property
    def level_count(self):
        return self._l_count

    @property
    def index(self):
        return self._rows

    @property
    def rows(self):
        return self._rows

    @property
    def hdates(self):
        return self._rows

    @property
    def row_count(self):
        return self._r_count

    @property
    def htypes(self):
        return self._columns

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
        """获取历史数据的一个切片，给定一个type、日期或股票代码

            contains three slice objects: htypes, share_pool, and hdates,

        input：
            :param keys: list/tuple/slice历史数据的类型名，为空时给出所有类型的数据
            参数row，str或pd.Timestamp，optional 历史数据的日期，为空时给出所有日期的数据
            参数share，str，optional：股票代码，为空时给出所有股票的数据
        输出：
            self.value的一个切片
        """

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
        else:
            htype_slice = slice(None, None, None)
            share_slice = slice(None, None, None)
            hdate_slice = slice(None, None, None)

        # check and convert each of the slice segments to the right type: a slice or \
        # a list of indices
        htype_slice = _make_list_or_slice(htype_slice, self.htypes)
        share_slice = _make_list_or_slice(share_slice, self.shares)
        hdate_slice = _make_list_or_slice(hdate_slice, self.hdates)

        print('share_pool is ', share_slice, '\nhtypes is ', htype_slice,
              '\nhdates is ', hdate_slice)
        return self.values[share_slice, hdate_slice, htype_slice]

    def __mul__(self, arg):
        self._values = self._values * arg
        return self

    def info(self):
        print(type(self))
        print(f'Levels: {self.level_count}, htypes: {self.column_count}')
        print(f'total {self.row_count} entries: ')

    def fillna(self, with_val):
        np._values = np.where(np.isnan(self._values), with_val, self._values)
        return self

    def to_dataframe(self, htype: str) -> pd.DataFrame:
        v = self._values[:, :, self.htypes[htype]].T
        return pd.DataFrame(v, index=list(self._rows.keys()), columns=list(self._levels.keys()))


def from_dataframe(df: pd.DataFrame = None):
    """ 根据DataFrame中的数据创建历史数据板HistoryPanel对象

    input:
        :param df:
    :return:
    """
    assert isinstance(df, pd.DataFrame), f'Input df should be pandas DataFrame! got {type(df)}.'
    return


def from_dataframes(*dfs):
    """ 根据多个DataFrame中的数据创建HistoryPanel对象

    input
    :param dfs: type list, containing multiple dataframes
    :return:
    """


def _make_list_or_slice(item, d):
    """

    :param item: slice or int/str or list of int/string
    :param d: a dictionary that contains strings as keys and integer as values
    :return:
        a list of slice that can be used to slice the Historical Data Object
    """
    if isinstance(item, slice):
        return item  # slice object can be directly used
    elif isinstance(item, int):  # number should be converted to a list containint itself
        return [item]
    elif isinstance(item, str):  # string should be converted to numbers
        return [d[item]]
    elif isinstance(item, list):
        res = []
        for i in item:  # convert all items into a number:
            res.extend(make_list_or_slice(i, d))
        return res
    else:
        return None


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

    # ==================
    # Historical Utility functions based on tushare
    # ==================

    def get_hist_rehab(self, share: str,
                       start: str,
                       end: str,
                       price_type: str = 'close',
                       asset_type: str = 'E',
                       adj: str = 'None',
                       freq: str = 'd',
                       ma: list = None)-> pd.DataFrame:
        """ get historical prices with rehabilitation rights
            获取指数或股票的复权历史价格

        input:
            :param price_type:
            :return:
            :param share:
            :param start:
            :param end:
            :param asset_type:
            :param adj:
            :param freq:
            :param ma:
        return:
            pd.DataFrame:
        """

        assert isinstance(share, str), f'share code should be a string, got {type(share)}'
        assert price_type in PRICE_TYPES, 'price types should be one of the predefined types'
        res = ts.pro_bar(ts_code=share, start_date=start, end_date=end, asset=asset_type, adj=adj, freq=freq, ma=ma)
        col_to_remove = list(col for col in res.columns if not col in price_type)
        res.drop(columns=col_to_remove, inline=True)
        assert isinstance(res, pd.DataFrame)
        return res

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
