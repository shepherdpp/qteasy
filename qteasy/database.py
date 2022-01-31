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
AVAILABLE_TABLES = []


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

    def overwrite_file(self, file_name, df):
        """ save df as file name or overwrite file name if file_name already exists

        :param file_name:
        :param df:
        :return:
        """
        if not isinstance(file_name, str):
            raise TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
        df = self.validated_dataframe(df)
        # df.to_csv(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        df.reset_index().to_feather(QT_ROOT_PATH + LOCAL_DATA_FOLDER + file_name + LOCAL_DATA_FILE_EXT)
        return file_name

    def extract_data(self, file_name, shares, start, end, freq: str = 'd'):
        """ 从文件中读取数据片段，指定股票代码、开始日期、结束日期和数据频率（数据频率必须低于文件所含数据的频率，否则会缺失数据

            数据中若存在NaN值，会原样返回

        :param file_name:   文件名
        :param shares:     需要读取的数据片段包含的股票代码
        :param start:      读取数据的开始日期时间
        :param end:        读取数据的结束日期时间
        :param freq:       读取数据的时间频率，该频率应该低于文件中所存储的数据的时间频率，例如
                                可以从频率为'd'的文件中读取'w'或者'q'的数据，反之则会出现缺失数据
        :return:
            DataFrame:     包含所需数据片段的DataFrame，行标签为日期时间，列标签为股票代码
        """
        expected_index = pd.date_range(start=start, end=end, freq=freq)
        expected_columns = shares

        df = self.open_file(file_name)

        index_missing = any(index not in df.index for index in expected_index)
        column_missing = any(column not in df.columns for column in expected_columns)

        if index_missing:
            additional_index = [index for index in expected_index if index not in df.index]
            df = df.reindex(expected_index)
            df.loc[additional_index] = np.inf

        if column_missing:
            additional_column = [c for c in expected_columns if c not in df.columns]
            # print(f'adding new columns {additional_column}')
            for col in additional_column:
                df[col] = np.inf

        extracted = df[expected_columns].loc[expected_index]

        return extracted

