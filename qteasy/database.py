# coding=utf-8
# database.py

# ======================================
# This file contains DataSource class, that
# maintains and manages local historical
# data in a specific folder, and provide
# seamless historical data operation for
# qteasy.
# ======================================

import pymysql
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from os import path
from qteasy import QT_ROOT_PATH

from .history import stack_dataframes, get_price_type_raw_data, get_financial_report_type_raw_data
from .utilfuncs import str_to_list, progress_bar

from ._arg_validators import PRICE_TYPE_DATA
from ._arg_validators import BALANCE_TYPE_DATA, CASHFLOW_TYPE_DATA
from ._arg_validators import INDICATOR_TYPE_DATA

LOCAL_DATA_FOLDER = 'qteasy/data/'
LOCAL_DATA_FILE_EXT = '.dat'

""" 
这里定义AVAILABLE_TABLES 以及 TABLE_STRUCTURES
"""
DATA_MAPPING_TABLE = []

# 定义Table structure，定义所有数据表的主键和内容
AVAILABLE_TABLES = {

    'trade_calendar':   {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_basic':      {'columns':     ['ts_code', 'symbol', 'name', 'area', 'industry', 'fullname',
                                         'enname', 'cnspell', 'market', 'exchange', 'curr_type',
                                         'list_status', 'list_date', 'delist_date', 'is_hs'],
                         'dtypes':      ['str', 'str', 'str', 'str', 'str', 'str', 'str', 'str',
                                         'str', 'str', 'str', 'str', 'str', 'str', 'str'],
                         'remarks':     ['TS代码', '股票代码', '股票名称', '地域', '所属行业', '股票全称',
                                         '英文全称', '拼音缩写', '市场类型（主板/创业板/科创板/CDR）',
                                         '交易所代码', '交易货币', '上市状态 L上市 D退市 P暂停上市',
                                         '上市日期', '退市日期', '是否沪深港通标的，N否 H沪股通 S深股通'],
                         'prime_keys':  [0]},

    'index_basic':      {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'fund_basic':       {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'future_basic':     {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'opt_basic':        {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_5min':       {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_30min':      {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_hourly':     {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_daily':      {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_weekly':     {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_monthly':    {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'index_daily':      {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'index_weekly':     {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'index_monthly':    {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'fund_daily':       {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'future_daily':     {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_adj_factor': {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_daily_info': {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'index_daily_info': {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'index_weight':     {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_income':     {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_balance':    {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_cashflow':    {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_financial':   {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_forecast':   {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]},

    'stock_express':    {'columns':     [],
                         'dtypes':      [],
                         'remarks':     [],
                         'prime_keys':  [0]}

}


class DataSource():
    """ DataSource 对象管理存储在本地的历史数据文件或数据库.

    通过DataSource对象，History模块可以容易地从本地存储的数据中读取并组装所需要的历史数据
    并确保历史数据符合HistoryPannel的要求。
    所有的历史数据必须首先从网络数据提供商处下载下来并存储在本地文件或数据库中，DataSource
    对象会检查数据的格式，确保格式正确并删除重复的数据。
    下载下来的历史数据可以存储成不同的格式，但是不管任何存储格式，所有数据表的结构都是一样
    的，而且都是与Pandas的DataFrame兼容的数据表格式。目前兼容的文件存储格式包括csv, hdf,
    ftr(feather)，兼容的数据库包括mysql和MariaDB。
    如果HistoryPanel所要求的数据未存放在本地，DataSource对象不会主动下载缺失的数据，仅会
    返回空DataFrame。
    DataSource对象可以按要求定期刷新或从NDP拉取数据，也可以手动操作

    """
    def __init__(self, **kwargs):
        """

        :param kwargs: the args can be improved in the future
        """
        pass

    def file_exists(self, file_name):
        """ returns whether a file exists or not

        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        return path.exists(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)

    def new_file(self, file_name, dataframe):
        """ create given dataframe into a new file with file_name

        :param dataframe:
        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        df = self.validated_dataframe(dataframe)

        if self.file_exists(file_name):
            raise FileExistsError(f'the file with name {file_name} already exists!')
        # dataframe.to_csv(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        dataframe.reset_index().to_feather(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        return file_name

    def del_file(self, file_name):
        """ delete file

        :param file_name:
        :return:
        """
        raise NotImplementedError

    def open_file(self, file_name):
        """ open the file with name file_name and return the df

        :param file_name:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        if not self.file_exists(file_name):
            raise FileNotFoundError(f'File {QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT} '
                                    f'not found!')

        # df = pd.read_csv(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT, index_col=0)
        df = pd.read_feather(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        df.index = df['date']
        df.drop(columns=['date'], inplace=True)
        df = self.validated_dataframe(df)
        return df

    # 以下函数是新架构所需要的
    def read_table_data(self):
        """

        """
        pass

    def write_table_data(self):
        """

        """
        pass

    def prep_table_data(self):
        """

        """
        pass

    # 以上函数是新架构需要的
