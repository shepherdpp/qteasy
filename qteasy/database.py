# coding=utf-8
# ======================================
# File:     database.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-11-29
# Desc:
#   Definition of DataSource class, managing
# local data storage and acquiring.
# ======================================

import os
from os import path
import pandas as pd
import numpy as np
import warnings

from functools import lru_cache

from .datatables import (
    AVAILABLE_DATA_FILE_TYPES,
    TABLE_MASTERS,
    get_table_master,
)

from .utilfuncs import (
    str_to_list,
    regulate_date_format,
    human_file_size,
    human_units,
    date_to_month_format,
    date_to_quarter_format,
)

from .datatables import (
    get_built_in_table_schema,
    set_primary_key_index,
    set_primary_key_frame,
)


class DataSource:
    """ DataSource 对象管理存储在本地的历史数据文件或数据库.

    通过DataSource对象，History模块可以容易地从本地存储的数据中读取并组装所需要的历史数据
    并确保历史数据符合HistoryPanel的要求。
    所有的历史数据必须首先从网络数据提供商处下载下来并存储在本地文件或数据库中，DataSource
    对象会检查数据的格式，确保格式正确并删除重复的数据。
    下载下来的历史数据可以存储成不同的格式，但是不管任何存储格式，所有数据表的结构都是一样
    的，而且都是与Pandas的DataFrame兼容的数据表格式。目前兼容的文件存储格式包括csv, hdf,
    fth(feather)，兼容的数据库包括mysql和MariaDB。
    如果HistoryPanel所要求的数据未存放在本地，DataSource对象不会主动下载缺失的数据，仅会
    返回空DataFrame。
    DataSource对象可以按要求定期刷新或从Provider拉取数据，也可以手动操作

    Attributes
    ----------

    Methods
    -------
    overview(print_out=True)
        以表格形式列出所有数据表的当前数据状态

    """

    def __init__(self,
                 source_type: str = 'file',
                 file_type: str = 'csv',
                 file_loc: str = 'data/',
                 host: str = 'localhost',
                 port: int = 3306,
                 user: str = None,
                 password: str = None,
                 db_name: str = 'qt_db',
                 allow_drop_table: bool = False):
        """ 创建一个DataSource 对象

        创建对象时确定本地数据存储方式，确定文件存储位置、文件类型，或者建立数据库的连接

        Parameters
        ----------
        source_type: str, Default: file
            数据源类型:
            - db/database: 数据存储在mysql数据库中
            - file: 数据存储在本地文件中
        file_type: str, {'csv', 'hdf', 'hdf5', 'feather', 'fth'}, Default: csv
            如果数据源为file时，数据文件类型：
            - csv: 简单的纯文本文件格式，可以用Excel打开，但是占用空间大，读取速度慢
            - hdf/hdf5: 基于pytables的数据表文件，速度较快，需要安装pytables
            - feather/fth: 轻量级数据文件，速度较快，占用空间小，需要安装pyarrow
        file_loc: str, Default: data/
            用于存储本地数据文件的路径
        host: str, default: localhost
            如果数据源为database时，数据库的host
        port: int, Default: 3306
            如果数据源为database时，数据库的port，默认3306
        user: str, Default: None
            如果数据源为database时，数据库的user name
        password: str, Default: None
            如果数据源为database时，数据库的passwrod
        db_name: str, Default: 'qt_db'
            如果数据源为database时，数据库的名称，默认值qt_db

        Raises
        ------
        ImportError
            部分文件格式以及数据类型需要optional dependency，如果缺乏这些package时，会提示安装
        SystemError
            数据类型为file时，在本地创建数据文件夹失败时会抛出该异常

        Returns
        -------
        None
        """
        if not isinstance(source_type, str):
            err = TypeError(f'source type should be a string, got {type(source_type)} instead.')
            raise err
        if source_type.lower() not in ['file', 'database', 'db']:
            err = ValueError(f'invalid source_type')
            raise err
        self._table_list = set()

        if source_type.lower() in ['db', 'database']:
            # try to create pymysql connections
            self.source_type = 'db'
            try:
                # optional packages to be imported
                import pymysql
                from dbutils.pooled_db import PooledDB

                # set up connection parameters to database
                assert isinstance(port, int), f'port should be int type, got {type(port)} instead!'
                assert user is not None, f'Missing user name for database connection'
                assert password is not None, f'Missing password for database connection'

                self.pool = PooledDB(
                        creator=pymysql,  # 使用链接数据库的模块
                        mincached=3,  # 初始化时，链接池中至少创建的链接，0表示不创建
                        maxconnections=5,  # 连接池允许的最大连接数，0和None表示不限制连接数
                        blocking=True,  # 连接池中如果没有可用连接后，是否阻塞等待。True，等待；False，不等待并报错
                        host=host,
                        port=port,
                        user=user,
                        password=password,
                        database=db_name,
                )
                self.connection_type = f'mysql://{host}@{port}/{db_name}'
                self.host = host
                self.port = port
                self.db_name = db_name
                self.file_type = None
                self.file_path = None
                self.__user__ = user
                self.__password__ = password

            except ImportError as e:
                msg = f'{str(e)}' \
                      f'Install pymysql or DButils: \n$ pip install pymysql\n$ pip install dbutils\n' \
                      f'Can not set data source type to "db", will fall back to csv file'

                warnings.warn(msg, RuntimeWarning, stacklevel=2)
                source_type = 'file'
                file_type = 'csv'

            except AssertionError as e:
                msg = f'Failed setting up mysql connection: {str(e)}\n' \
                      f'Can not set data source type to "db", will fall back to csv file'

                warnings.warn(msg, RuntimeWarning, stacklevel=2)
                source_type = 'file'
                file_type = 'csv'

            except Exception as e:
                msg = f'Mysql connection failed: {str(e)}\n' \
                      f'Can not set data source type to "db", will fall back to csv file'

                warnings.warn(msg, RuntimeWarning, stacklevel=2)
                source_type = 'file'
                file_type = 'csv'

            finally:
                pass

        if source_type.lower() == 'file':
            from qteasy import QT_ROOT_PATH
            try:
                file_type = file_type.lower()
                assert file_type in AVAILABLE_DATA_FILE_TYPES, (f'Wrong file type!'
                                                                f'supported file types are {AVAILABLE_DATA_FILE_TYPES}')
                if file_type in ['hdf']:
                    import tables
                    file_type = 'hdf'
                if file_type in ['feather', 'fth']:
                    import pyarrow
                    file_type = 'fth'

                self.file_path = path.join(QT_ROOT_PATH, file_loc)
                os.makedirs(self.file_path, exist_ok=True)  # 确保数据dir不存在时创建一个
            except AssertionError as e:
                err = AssertionError(f'{str(e)}')
                raise err
            except TypeError as e:
                err = TypeError(f'{str(e)}, file type should be a string, got {type(file_type)} instead!')
                raise err
            except ImportError as e:
                msg = f'Missing optional dependency \'pytables\' for datasource file type ' \
                      f'\'hdf\'. Please install pytables: $ conda install pytables\n' \
                      f'Can not create data source with file type {file_type}, will fall back to csv file'
                warnings.warn(msg, RuntimeWarning, stacklevel=2)

                file_type = 'csv'
            except Exception as e:
                err = SystemError(f'{str(e)}, Failed creating data directory \'{file_loc}\' in qt root path, '
                                  f'please check your input.')
                raise err

            self.source_type = 'file'
            self.file_type = file_type
            self.file_loc = file_loc
            self.connection_type = f'file://{file_type}@qt_root/{file_loc}'
            self.host = None
            self.port = None
            self.db_name = None
            self.__user__ = None
            self.__password__ = None

        self._allow_drop_table = allow_drop_table

    @property
    def tables(self) -> list:
        """ 所有已经建立的tables的清单"""
        return list(self._table_list)

    @property
    def all_tables(self) -> list:
        """ 获取所有数据表的清单"""
        return get_table_master().index.to_list()

    @property
    def all_sys_tables(self) -> list:
        """ 获取所有系统数据表的清单"""
        tables = get_table_master()
        return tables[tables['table_usage'] == 'sys'].index.to_list()

    def none_sys_tables(self) -> list:
        """ 获取所有非系统数据表的清单"""
        tables = get_table_master()
        return tables[tables['table_usage'] != 'sys'].index.to_list()

    @property
    def all_data_tables(self) -> list:
        """ 获取所有历史数据表（不包括调整表）的清单"""
        tables = get_table_master()
        return tables[~tables['table_usage'].isin(['sys', 'adj'])].index.to_list()

    @property
    def all_basic_tables(self) -> list:
        """ 获取所有基础数据表的清单"""
        tables = get_table_master()
        return tables[tables['table_usage'] == 'basics'].index.to_list()

    @property
    def allow_drop_table(self) -> bool:
        """ 获取是否允许删除数据表"""
        return self._allow_drop_table

    @allow_drop_table.setter
    def allow_drop_table(self, value: bool):
        """ 设置是否允许删除数据表"""
        if not isinstance(value, bool):
            err = TypeError(f'allow_drop_table should be a boolean, got {type(value)} instead!')
            raise err
        self._allow_drop_table = value

    def __repr__(self):
        if self.source_type == 'db':
            return f'DataSource(\'db\', \'{self.host}\', {self.port})'
        elif self.source_type == 'file':
            return f'DataSource(\'file\', \'{self.file_type}\', \'{self.file_loc}\')'
        else:
            return

    def __str__(self):
        return self.connection_type

    def info(self):
        """ 格式化打印database对象的各种主要信息

        Returns
        -------
        """
        if self.source_type == 'file':
            print(f'DataSource Info: \n'
                  f'{"=" * 40}\n'
                  f'{"Source Type":<20}: {self.source_type}\n'
                  f'{"File Type":<20}: {self.file_type}\n'
                  f'{"File Location":<20}: {self.file_loc}\n')
        elif self.source_type == 'db':
            print(f'DataSource Info: \n'
                  f'{"=" * 40}\n'
                  f'{"Source Type":<20}: {self.source_type}\n'
                  f'{"Host":<20}: {self.host}\n'
                  f'{"Port":<20}: {self.port}\n'
                  f'{"User":<20}: {self.__user__}\n'
                  f'{"Database":<20}: {self.db_name}\n')

    def overview(self, tables=None, print_out=True, include_sys_tables=False) -> pd.DataFrame:
        """ 以表格形式列出所有数据表的当前数据状态

        Parameters
        ----------
        tables: str or list of str, Default None
            指定要列出的数据表，如果为None则列出所有数据表
        print_out: bool, Default True
            是否打印数据表总揽
        include_sys_tables: bool, Default False
            是否包含系统表

        Returns
        -------
        pd.DataFrame, 包含所有数据表的数据状态
        """

        all_tables = get_table_master()
        if not include_sys_tables:
            all_tables = all_tables[all_tables['table_usage'] != 'sys']
        all_table_names = all_tables.index
        if tables is not None:
            if isinstance(tables, str):
                tables = str_to_list(tables)
            if not isinstance(tables, list):
                err = TypeError(f'tables should be a list of str, got {type(tables)} instead!')
                raise err
            all_table_names = [table_name for table_name in all_table_names if table_name in tables]

        all_info = []
        print('Analyzing local data source tables... depending on size of tables, it may take a few minutes')
        total_table_count = len(all_table_names)
        from .utilfuncs import progress_bar
        completed_reading_count = 0
        for table_name in all_table_names:
            progress_bar(completed_reading_count, total_table_count, comments=f'Analyzing table: <{table_name}>')
            all_info.append(self.get_table_info(table_name, verbose=False, print_info=False, human=True).values())
            completed_reading_count += 1
        progress_bar(completed_reading_count, total_table_count, comments=f'Analyzing completed!')
        all_info = pd.DataFrame(all_info, columns=['table', 'has_data', 'size', 'records',
                                                   'pk1', 'records1', 'min1', 'max1',
                                                   'pk2', 'records2', 'min2', 'max2'])
        all_info.index = all_info['table']
        all_info.drop(columns=['table'], inplace=True)
        if print_out:
            info_to_print = all_info.loc[all_info.has_data == True][['has_data', 'size', 'records', 'min2', 'max2']]
            print(f'\nFinished analyzing datasource: \n{self}\n'
                  f'{len(info_to_print)} table(s) out of {len(all_info)} contain local data as summary below, '
                  f'to view complete list, print returned DataFrame\n'
                  f'{"tables with local data":=^84}')
            print(info_to_print.to_string(columns=['has_data',
                                                   'size',
                                                   'records',
                                                   'min2',
                                                   'max2'],
                                          header=['Has_data',
                                                  'Size_on_disk',
                                                  'Record_count',
                                                  'Record_start',
                                                  'Record_end'],
                                          justify='center'
                                          )
                  )
        return all_info

    # 文件操作层函数，只操作文件，不修改数据
    def _get_file_path_name(self, file_name):
        """获取完整文件路径名"""
        if self.source_type == 'db':
            err = RuntimeError('can not check file system while source type is "db"')
            raise err
        if not isinstance(file_name, str):
            err = TypeError(f'file_name name must be a string, {file_name} is not a valid input!')
            raise err
        file_name = file_name + '.' + self.file_type
        file_path_name = path.join(self.file_path, file_name)
        return file_path_name

    def _file_exists(self, file_name):
        """ 检查文件是否已存在

        Parameters
        ----------
        file_name: 需要检查的文件名(不含扩展名)
        Returns
        -------
        Boolean: 文件存在时返回真，否则返回假
        """
        file_path_name = self._get_file_path_name(file_name)
        return path.exists(file_path_name)

    def _write_file(self, df, file_name):
        """ 将df写入本地文件，在把文件写入文件之前，需要将primary key写入index，使用
        set_primary_key_index()函数

        Parameters
        ----------
        df: 待写入文件的DataFrame,primary key 为index
        file_name: 本地文件名(不含扩展名)
        Returns
        -------
        str: file_name 如果数据保存成功，返回完整文件路径名称
        """
        file_path_name = self._get_file_path_name(file_name)
        if self.file_type == 'csv':
            df.to_csv(file_path_name, encoding='utf-8')
        elif self.file_type == 'fth':
            df.reset_index().to_feather(file_path_name)
        elif self.file_type == 'hdf':
            df.to_hdf(file_path_name, key='df')
        else:  # for some unexpected cases
            err = TypeError(f'Invalid file type: {self.file_type}')
            raise err
        return len(df)

    def _read_file(self, file_name, primary_key, pk_dtypes, share_like_pk=None,
                   shares=None, date_like_pk=None, start=None, end=None, chunk_size=50000):
        """ 从文件中读取DataFrame，当文件类型为csv时，支持分块读取且完成数据筛选

        Parameters
        ----------
        file_name: str
            文件名
        primary_key: list of str
            用于生成primary_key index 的主键
        pk_dtypes: list of str
            primary_key的数据类型
        share_like_pk: str
            用于按值筛选数据的主键
        shares: list of str
            用于筛选数据的主键的值
        date_like_pk: str
            用于按日期筛选数据的主键
        start: datetime-like
            用于按日期筛选数据的起始日期
        end: datetime-like
            用于按日期筛选数据的结束日期
        chunk_size: int
            分块读取csv大文件时的分块大小

        Returns
        -------
        DataFrame：从文件中读取的DataFrame，如果数据有主键，将主键设置为df的index
        """

        # TODO: 历史数据表的规模较大，如果数据存储在数据库中，读取和存储时
        #  没有问题，但是如果数据存储在文件中，需要优化存储和读取过程
        #  ，以便提高效率。目前优化了csv文件的读取，通过分块读取提高
        #  csv文件的读取效率，其他文件系统的读取还需要进一步优化

        file_path_name = self._get_file_path_name(file_name)
        if not self._file_exists(file_name):
            # 如果文件不存在，则返回空的DataFrame
            return pd.DataFrame()
        if date_like_pk is not None:
            start = pd.to_datetime(start).strftime('%Y-%m-%d')
            end = pd.to_datetime(end).strftime('%Y-%m-%d')

        if self.file_type == 'csv':
            # 这里针对csv文件进行了优化，通过分块读取文件，避免当文件过大时导致读取异常
            try:
                df_reader = pd.read_csv(file_path_name, chunksize=chunk_size)
            except FileNotFoundError:
                raise FileNotFoundError(f'File {file_name} not found!')
            except FileExistsError:
                raise FileExistsError(f'File {file_name} exists but can not be read!')
            except Exception as e:
                err = RuntimeError(f'{e}, file reading error encountered.')
                raise err
            df_picker = (chunk for chunk in df_reader)
            if (share_like_pk is not None) and (date_like_pk is not None):
                df_picker = (chunk.loc[(chunk[share_like_pk].isin(shares)) &
                                       (chunk[date_like_pk] >= start) &
                                       (chunk[date_like_pk] <= end)] for chunk in df_reader)
            elif (share_like_pk is None) and (date_like_pk is not None):
                df_picker = (chunk.loc[(chunk[date_like_pk] >= start) &
                                       (chunk[date_like_pk] <= end)] for chunk in df_reader)
            elif (share_like_pk is not None) and (date_like_pk is None):
                df_picker = (chunk.loc[(chunk[share_like_pk].isin(shares))] for chunk in df_reader)
            df = pd.concat(df_picker)
            set_primary_key_index(df, primary_key=primary_key, pk_dtypes=pk_dtypes)

            return df

        if self.file_type == 'hdf':
            # TODO: hdf5/feather的大文件读取尚未优化
            try:
                df = pd.read_hdf(file_path_name, 'df')
            except ValueError as e:
                if 'pickle protocol: 5' in e.__str__():  # check when the file is written in a higher pickle protocol
                    err = EnvironmentError(f'File {file_name} is written in a higher version of python which uses '
                                           f'pickle protocol 5, to avoid this error, install pickle5 package and '
                                           f're-save the file.')
                    raise err
                else:
                    err = RuntimeError(f'{e}, file reading error encountered.')
                    raise err
            except Exception as e:
                err = RuntimeError(f'{e}, file reading error encountered.')
                raise err

            df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtypes)
        elif self.file_type == 'fth':
            # TODO: feather大文件读取尚未优化
            try:
                df = pd.read_feather(file_path_name)
            except Exception as e:
                err = RuntimeError(f'{e}, file reading error encountered.')
                raise err
        else:  # for some unexpected cases
            err = TypeError(f'Invalid file type: {self.file_type}')
            raise err

        try:
            # 如果self.file_type 为 hdf/fth，那么需要筛选数据
            if (share_like_pk is not None) and (date_like_pk is not None):
                df = df.loc[(df[share_like_pk].isin(shares)) &
                            (df[date_like_pk] >= start) &
                            (df[date_like_pk] <= end)]
            elif (share_like_pk is None) and (date_like_pk is not None):
                df = df.loc[(df[date_like_pk] >= start) &
                            (df[date_like_pk] <= end)]
            elif (share_like_pk is not None) and (date_like_pk is None):
                df = df.loc[(df[share_like_pk].isin(shares))]
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e

        set_primary_key_index(df, primary_key=primary_key, pk_dtypes=pk_dtypes)
        return df

    def _delete_file_records(self, file_name, primary_key, record_ids) -> int:
        """ 从文件中删除指定的记录

        Parameters
        ----------
        file_name: str
            文件名
        primary_key: list of str
            主键
        record_ids: list of int or tuple of int
            待删除的记录的主键值

        Returns
        -------
        rows_deleted: int
            删除的记录数
        """
        # check that all record_ids are integers
        if not all(isinstance(record_id, int) for record_id in record_ids):
            err = TypeError(f'All record_ids must be integers, got {record_ids} instead!')
            raise err
        # read all data from file into a dataframe
        primary_key = [primary_key] if isinstance(primary_key, str) else primary_key
        df = self._read_file(file_name, primary_key, pk_dtypes=['int'])
        # check if the record_ids are in the dataframe, remove them if they are
        rows_deleted = 0
        for record_id in record_ids:
            if record_id in df.index:
                df.drop(record_id, inplace=True)
                rows_deleted += 1

        # write the updated dataframe back to the file, make sure primary keys are in index
        df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=['int'])
        set_primary_key_index(df, primary_key=primary_key, pk_dtypes=['int'])
        self._write_file(df, file_name)

        return rows_deleted

    def _get_file_table_coverage(self, table, column, primary_key, pk_dtypes, min_max_only):
        """ 检查数据表文件关键列的内容，去重后返回该列的内容清单

        Parameters
        ----------
        table: str
            数据表名
        column: str
            关键列名
        primary_key: list of str
            数据表的主键名称列表
        pk_dtypes: list of str
            数据表的主键数据类型列表
        min_max_only: bool
            为True时仅输出最小、最大以及总数量，False输出完整列表

        Returns
        -------
        list of str
            数据表中存储的数据关键列的清单
        """
        if not self._file_exists(table):
            return list()
        df = self._read_file(table, primary_key, pk_dtypes)
        if df.empty:
            return list()
        if column in list(df.index.names):
            extracted_val = df.index.get_level_values(column).unique()
        else:
            extracted_val = df[column].unique()
        if isinstance(extracted_val[0], pd.Timestamp):
            extracted_val = extracted_val.strftime('%Y%m%d')

        res = list()
        if min_max_only:
            res.append(extracted_val.min())
            res.append(extracted_val.max())
            res.append(len(extracted_val))
        else:
            res.extend(extracted_val)

        return list(res)

    def _drop_file(self, file_name):
        """ 删除本地文件

        Parameters
        ----------
        file_name: str
            将被删除的文件名

        Returns
        -------
        None
        """
        import os
        if self._file_exists(file_name):
            file_path_name = os.path.join(self.file_path, file_name + '.' + self.file_type)
            os.remove(file_path_name)

    def _get_file_size(self, file_name):
        """ 获取文件大小，输出

        Parameters
        ----------
        file_name:  str 文件名
        Returns
        -------
            str representing file size
        """
        import os
        file_path_name = self._get_file_path_name(file_name)
        try:
            file_size = os.path.getsize(file_path_name)
            return file_size
        except FileNotFoundError:
            return -1
        except Exception as e:
            err = RuntimeError(f'{e}, unknown error encountered.')
            raise err

    def _get_file_rows(self, file_name):
        """获取csv、hdf、feather文件中数据的行数"""
        file_path_name = self._get_file_path_name(file_name)
        if self.file_type == 'csv':
            with open(file_path_name, 'r', encoding='utf-8') as fp:
                line_count = None
                for line_count, line in enumerate(fp):
                    pass
                return line_count
        elif self.file_type == 'hdf':
            df = pd.read_hdf(file_path_name, 'df')
            return len(df)
        elif self.file_type == 'fth':
            df = pd.read_feather(file_path_name)
            return len(df)

    # 数据库操作层函数，只操作具体的数据表，不操作数据
    def _db_open_connection(self):
        """从数据连接池中获取数据连接，返回con和cursor对象"""
        try:
            conn = self.pool.connection()
            cursor = conn.cursor()  # 表示读取的数据为字典类型
            return conn, cursor
        except Exception as e:
            err = RuntimeError(f'{e}, error in opening database connection')
            return None, None

    @staticmethod
    def _db_close_connection(conn, cursor):
        """关闭数据库连接"""
        cursor.close()
        conn.close()

    def _db_execute_one(self, sql, data=None, *, fetch_and_return=True, return_cursor=False, rollback=False) -> any:
        """从mysql连接池获取一个新的连接，执行一条sql语句， 返回结果并关闭连接

        Parameters
        ----------
        sql: str
            需要执行的sql语句
        data: tuple, optional,
            需要执行的数据
        fetch_and_return: bool, Default True
            是否需要返回执行sql语句的结果
        return_cursor: bool, Default False
            是否需要同时返回cursor对象，默认不需要，如果fetch_and_return为False，则无效
        rollback: bool, Default False
            是否在执行sql语句出错时回滚

        Returns
        -------
        result: any
            执行sql语句的结果
        """
        conn, cursor = self._db_open_connection()
        try:
            rows_affected = cursor.execute(sql, data)
            conn.commit()
            if fetch_and_return:
                result = cursor.fetchall()
                if return_cursor:
                    return result, cursor
                else:
                    return result
            return rows_affected
        except Exception as e:
            if rollback:
                conn.rollback()
            err = RuntimeError(f'{e}, error in executing sql: {sql}')
            raise err
        finally:
            self._db_close_connection(conn, cursor)

    def _db_execute_many(self, sql, data, rollback=False) -> any:
        """从mysql连接池获取一个新的连接，执行包含多条数据的sql语句，返回执行的结果并关闭连接

        Parameters
        ----------
        sql: str
            需要执行的sql语句
        data: tuple of tuple
            需要执行的数据
        rollback: bool, Default False
            是否在执行sql语句出错时回滚

        Returns
        -------
        rows_affected: int: 执行sql语句的结果
        """
        conn, cursor = self._db_open_connection()
        try:
            rows_affected = cursor.executemany(sql, data)
            conn.commit()
            return rows_affected
        except Exception as e:
            if rollback:
                conn.rollback()
            err = RuntimeError(f'{e}, error in executing sql: {sql}')
            raise err
        finally:
            self._db_close_connection(conn, cursor)

    def _read_database(self, db_table, share_like_pk=None, shares=None, date_like_pk=None, start=None, end=None):
        """ 从一张数据库表中读取数据，读取时根据share(ts_code)和dates筛选
            具体筛选的字段通过share_like_pk和date_like_pk两个字段给出

        Parameters
        ----------
        db_table: str
            需要读取数据的数据表
        share_like_pk: str
            用于筛选证券代码的字段名，不同的表中字段名可能不同，用这个字段筛选不同的证券、如股票、基金、指数等
            当这个参数给出时，必须给出shares参数
        shares: str,
            如果给出shares，则按照"WHERE share_like_pk IN shares"筛选
        date_like_pk: str
            用于筛选日期的主键字段名，不同的表中字段名可能不同，用这个字段筛选需要的记录的时间段
            当这个参数给出时，必须给出start和end参数
        start: datetime like,
            如果给出start同时又给出end，按照"WHERE date_like_pk BETWEEN start AND end"的条件筛选
        end: datetime like,
            当没有给出start时，单独给出end无效

        Returns
        -------
            DataFrame，从数据库中读取的DataFrame
        """
        if not self._db_table_exists(db_table):
            return pd.DataFrame()
        ts_code_filter = ''
        has_ts_code_filter = False
        date_filter = ''
        has_date_filter = False
        if shares is not None:
            has_ts_code_filter = True
            share_count = len(shares)
            if share_count > 1:
                ts_code_filter = f'{share_like_pk} in {tuple(shares)}'
            else:
                ts_code_filter = f'{share_like_pk} = "{shares[0]}"'
        if (start is not None) and (end is not None):
            # assert start and end are date-like
            has_date_filter = True
            date_filter = f'{date_like_pk} BETWEEN "{start}" AND "{end}"'

        sql = f'SELECT * ' \
              f'FROM {db_table}\n'
        if not (has_ts_code_filter or has_date_filter):
            # No WHERE clause
            pass
        elif has_ts_code_filter and has_date_filter:
            # both WHERE clause for ts_code and date
            sql += f'WHERE {ts_code_filter}' \
                   f' AND {date_filter}\n'
        elif has_ts_code_filter and not has_date_filter:
            # only one WHERE clause for ts_code
            sql += f'WHERE {ts_code_filter}\n'
        elif not has_ts_code_filter and has_date_filter:
            # only one WHERE clause for date
            sql += f'WHERE {date_filter}'
        sql += ''

        res, cursor = self._db_execute_one(sql, return_cursor=True)
        df = pd.DataFrame(res, columns=[i[0] for i in cursor.description])
        return df

    def _write_database(self, df, db_table, primary_key):
        """ 将DataFrame中的数据添加到数据库表末尾，如果表不存在，则
        新建一张数据库表，并设置primary_key（如果给出）

        假定df的列与db_table的schema相同且顺序也相同

        Parameter
        ---------
        df: pd.DataFrame
            需要添加的DataFrame
        db_table: str
            需要添加数据的数据库表
        primary_key: tuple
            数据表的primary_key，必须定义在数据表中

        Returns
        -------
        int: 返回写入的记录数

        Note
        ----
        调用update_database()执行任务，设置参数ignore_duplicate=True
        """

        # if table does not exist, create a new table without primary key info
        if not self._db_table_exists(db_table):
            dtype_mapping = {'object':         'varchar(255)',
                             'datetime64[ns]': 'datetime',
                             'int64':          'int',
                             'float32':        'float',
                             'float64':        'double',
                             }
            columns = df.columns
            dtypes = df.dtypes.tolist()
            dtypes = [dtype_mapping.get(str(dtype.name), 'varchar(255)') for dtype in dtypes]
            # create a new table
            self._new_db_table(
                    db_table=db_table,
                    columns=columns,
                    dtypes=dtypes,
                    primary_key=primary_key)

        tbl_columns = tuple(self._get_db_table_schema(db_table).keys())
        # TODO:
        #  实际上，下面的代码与update_database()中的代码几乎一样
        #  应该将这一大坨代码抽象出来，作为一个单独的函数，统一调用
        if (len(df.columns) != len(tbl_columns)) or (any(i_d != i_t for i_d, i_t in zip(df.columns, tbl_columns))):
            raise KeyError(f'df columns {df.columns.to_list()} does not fit table schema {list(tbl_columns)}')
        df = df.where(pd.notna(df), None)  # where-fill None in dataframe result in filling np.nan since pandas v2.0
        pd_version = pd.__version__
        if pd_version >= '2.0':
            df.replace(np.nan, None, inplace=True)
        df_tuple = tuple(df.itertuples(index=False, name=None))
        sql = f"INSERT IGNORE INTO "
        sql += f"`{db_table}` ("
        for col in tbl_columns[:-1]:
            sql += f"`{col}`, "
        sql += f"`{tbl_columns[-1]}`)\nVALUES\n("
        for val in tbl_columns[:-1]:
            sql += "%s, "
        sql += "%s)\n"

        rows_affected = self._db_execute_many(sql, df_tuple)
        return rows_affected

    def _update_database(self, df, db_table, primary_key):
        """ 用DataFrame中的数据更新数据表中的数据记录

        假定df的列与db_table的列相同且顺序也相同
        在插入数据之前，必须确保表的primary_key已经正确设定
        如果写入记录的键值存在冲突时，更新数据库中的记录

        Parameters
        ----------
        df: pd.DataFrame
            用于更新数据表的数据DataFrame
        db_table: str
            需要更新的数据表
        primary_key: tuple
            数据表的primary_key，必须定义在数据表中，如果数据库表没有primary_key，将append所有数据

        Returns
        -------
        int: rows affected
        """
        tbl_columns = tuple(self._get_db_table_schema(db_table).keys())
        update_cols = [item for item in tbl_columns if item not in primary_key]
        # 确保df的列与数据库表的列相同
        if (len(df.columns) != len(tbl_columns)) or (any(i_d != i_t for i_d, i_t in zip(df.columns, tbl_columns))):
            raise KeyError(f'df columns {df.columns.to_list()} does not fit table schema {list(tbl_columns)}')
        df = df.where(pd.notna(df), None)  # fill None in Dataframe will result in filling Nan since pandas v2.0
        pd_version = pd.__version__
        if pd_version >= '2.0':
            df.replace(np.nan, None, inplace=True)
            # TODO, 在某些情况下将数据写入数据库时仍然会发生'nan can't be written to mysql'的错误
            #  这个问题需要进一步解，复现代码如下：
            #  op=qt.Operator('dma')
            #  op.run(mode=0, live_trade_account_id=1, asset_type='IDX')

        df_tuple = tuple(df.itertuples(index=False, name=None))
        sql = f"INSERT INTO "
        sql += f"`{db_table}` ("
        for col in tbl_columns[:-1]:
            sql += f"`{col}`, "
        sql += f"`{tbl_columns[-1]}`)\nVALUES\n("
        for val in tbl_columns[:-1]:
            sql += "%s, "
        sql += "%s)\n" \
               "ON DUPLICATE KEY UPDATE\n"
        for col in update_cols[:-1]:
            sql += f"`{col}`=VALUES(`{col}`),\n"
        sql += f"`{update_cols[-1]}`=VALUES(`{update_cols[-1]}`)"

        rows_affected = self._db_execute_many(sql, df_tuple)
        return rows_affected

    def _delete_database_records(self, db_table, primary_key, record_ids):
        """ 从数据库表中删除数据

        必须给出数据表的主键名，以及需要删除的记录的主键值

        Parameters
        ----------
        db_table: str
            数据表名
        primary_key: str
            数据表的主键名称列表
        record_ids: list of str or tuple of str
            需要删除的记录的主键值

        Returns
        -------
        int: rows affected
        """
        # 如果没有记录需要删除，则直接返回
        if not record_ids:
            return 0

        # 生成删除记录的SQL语句
        sql = f"DELETE FROM `{db_table}` WHERE "
        # 设置删除的条件
        if len(record_ids) > 1:
            sql += f"`{primary_key}` IN {tuple(record_ids)}"
        elif len(record_ids) == 1:
            sql += f"`{primary_key}` = {record_ids[0]}"

        rows_affected = self._db_execute_one(sql, fetch_and_return=False)
        return rows_affected

    def _get_db_table_coverage(self, db_table, column):
        """ 检查数据库表关键列的内容，去重后返回该列的内容清单

        Parameters
        ----------
        db_table: str
            数据表名
        column: str
            数据表的字段名

        Returns
        -------
        """
        import datetime
        if not self._db_table_exists(db_table):
            return list()
        sql = f'SELECT DISTINCT `{column}`' \
              f'FROM `{db_table}`' \
              f'ORDER BY `{column}`'
        res = self._db_execute_one(sql)
        res = [item[0] for item in res]
        if isinstance(res[0], datetime.datetime):
            res = list(pd.to_datetime(res).strftime('%Y%m%d'))
        return res

    def _get_db_table_minmax(self, db_table, column, with_count=False):
        """ 检查数据库表关键列的内容，获取最小值和最大值和总数量

        Parameters
        ----------
        db_table: str
            数据表名
        column: str
            数据表的字段名
        with_count: bool, default False
            是否返回关键列值的数量，可能非常耗时

        Returns
        -------
        list: [min, max, count]
        """
        import datetime
        if not self._db_table_exists(db_table):
            return list()
        if with_count:
            add_sql = f', COUNT(DISTINCT(`{column}`))'
        else:
            add_sql = ''
        sql = f'SELECT MIN(`{column}`), MAX(`{column}`){add_sql} '
        sql += f'FROM `{db_table}`'

        res = self._db_execute_one(sql)[0]
        res = list(res)
        if isinstance(res[0], datetime.datetime):
            res = list(pd.to_datetime(res).strftime('%Y%m%d'))
        return res

    def _db_table_exists(self, db_table):
        """ 检查数据库中是否存在db_table这张表

        Parameters
        ----------
        db_table: str
            数据表名

        Returns
        -------
        bool
        """
        sql = f"SHOW TABLES LIKE '{db_table}'"
        res = self._db_execute_one(sql)
        if res is not None:
            return len(res) > 0
        else:
            return False

    def _new_db_table(self, db_table, columns, dtypes,
                      primary_key: [str],
                      auto_increment_id: bool = False,
                      index_col: [str] = None,
                      partition_by: [str] = None,
                      partitions: int = None) -> None:
        """ 在数据库中新建一个数据表(如果该表不存在)，并且确保数据表的schema与设置相同,
            并创建正确的index

        Parameters
        ----------
        db_table: str
            数据表名
        columns: list of str
            数据表的所有字段名
        dtypes: list of str {'varchar', 'float', 'int', 'datetime', 'text'}
            数据表所有字段的数据类型
        primary_key: list of str
            数据表的所有primary_key
        auto_increment_id: bool, Default: False
            是否使用自增主键
        index_col: list of str, Default: None
            数据表的索引列
        partition_by: list of str, Default: None
            数据表的分区列
        partitions: int, Default: None
            数据表的分区数

        Returns
        -------
        None
        """

        sql = f"CREATE TABLE IF NOT EXISTS `{db_table}` (\n"
        for col_name, dtype in zip(columns, dtypes):
            sql += f"`{col_name}` {dtype}"
            if col_name in primary_key:
                sql += " NOT NULL"
                sql += " AUTO_INCREMENT,\n" if auto_increment_id else ",\n"
            else:
                sql += " DEFAULT NULL,\n"
        # 如果有primary key则添加primary key
        if primary_key is not None:
            sql += f"PRIMARY KEY (`{'`, `'.join(primary_key)}`)"
            # 如果primary key多于一个，则创建KEY INDEX
            if len(primary_key) > 1:
                sql += ",\nKEY (`" + '`),\nKEY (`'.join(primary_key[1:]) + "`)"
        sql += '\n)'

        # 如果设置了partition则添加partition by KEY()
        if partition_by is not None:
            sql += f"PARTITION BY KEY(`{partition_by}`) PARTITIONS {partitions}"

        # 执行sql语句
        self._db_execute_one(sql, fetch_and_return=False)

        # 如果设置了额外的index则添加index:
        # TODO: 使用KEY关键字添加额外的index
        # if index_col is not None:
        #     sql = f"CREATE INDEX `{db_table}_idx` ON `{db_table}` (`{index_col}`)"
        #
        #     # 执行sql语句
        #     self._db_execute_one(sql, fetch_and_return=False)

    # ==============
    # 特殊数据库操作层函数，当数据表结构发生变化时用于调整数据库表结构，建立索引或执行分区等操作
    def _get_db_table_schema(self, db_table):
        """ 获取数据库表的列名称和数据类型

        Parameters
        ----------
        db_table: str
            需要获取列名的数据库表

        Returns
        -------
            dict: 一个包含列名和数据类型的Dict: {column1: dtype1, column2: dtype2, ...}
        """

        sql = f"SELECT COLUMN_NAME, DATA_TYPE " \
              f"FROM INFORMATION_SCHEMA.COLUMNS " \
              f"WHERE TABLE_SCHEMA = Database() " \
              f"AND table_name = '{db_table}' " \
              f"ORDER BY ordinal_position;"

        result = self._db_execute_one(sql)
        columns = {}
        if len(result[0]) == 0:
            return columns
        for col, typ in result:
            columns[col] = typ
        return columns

    def _drop_db_table(self, db_table):
        """ 修改优化db_table的schema，建立index，从而提升数据库的查询速度提升效能

        Parameters
        ----------
        db_table: str
            数据表名

        Returns
        -------
        None
        """

        sql = f"DROP TABLE IF EXISTS {db_table};"

        self._db_execute_one(sql, fetch_and_return=False)

    def _get_db_table_size(self, db_table):
        """ 获取数据库表的占用磁盘空间

        Parameters
        ----------
        db_table: str
            数据库表名称

        Returns
        -------
        rows: int
        """
        if not self._db_table_exists(db_table):
            return -1

        sql = "SELECT table_rows, data_length + index_length " \
              "FROM INFORMATION_SCHEMA.tables " \
              "WHERE table_schema = %s " \
              "AND table_name = %s;"
        rows, size = self._db_execute_one(sql, (self.db_name, db_table), fetch_and_return=True)[0]
        return rows, size

    def _alter_db_table(self, db_table, columns, dtypes, primary_key, auto_increment_id=False):
        """ 修改数据库表的schema，建立index，从而提升数据库的查询速度提升效能
        """
        raise NotImplementedError

    def _alter_db_table_index(self, db_table, index_name, columns, unique=False):
        """ 修改数据库表的schema，建立index，从而提升数据库的查询速度提升效能
        """
        raise NotImplementedError

    def _alter_db_table_partition(self, db_table, partition_name, partition_type, partition_key):
        """ 修改数据库表的schema，建立index，从而提升数据库的查询速度提升效能
        """
        raise NotImplementedError

    # ==============
    # (逻辑)数据表操作层函数，只在逻辑表层面读取或写入数据，调用文件操作函数或数据库函数存储数据
    def table_data_exists(self, table):
        """ 逻辑层函数，判断数据表是否存在

        Parameters
        ----------
        table: 数据表名称

        Returns
        -------
        bool: True if table exists, False otherwise
        """
        if self.source_type == 'db':
            return self._db_table_exists(db_table=table)
        elif self.source_type == 'file':
            return self._file_exists(table)
        else:
            raise KeyError(f'invalid source_type: {self.source_type}')

    @lru_cache(maxsize=32)
    def read_cached_table_data(
            self,
            table: str, *,
            shares: str = None,
            start: str = None,
            end: str = None,
            primary_key_in_index: bool = True,
    ) -> pd.DataFrame:
        """ 缓存数据表数据以缩短读取速度，这个函数用于加快本地提取数据时加速

        在用户使用DataType对象大量读取数据时，通常需要重复从同一张数据表中以同样的参数获取数据
        为了提升读取速度，可以将数据表的数据缓存到内存中，以减少读取时间，但在正常的数据表操作中
        并不适合使用缓存，因为数据表通常需要实时刷新，因此本函数仅供DataType对象读取数据使用
        """

        return self.read_table_data(
                table,
                shares=shares,
                start=start,
                end=end,
                primary_key_in_index=primary_key_in_index,
        )

    def read_table_data(self, table, *,
                        shares: str = None,
                        start: str = None,
                        end: str = None,
                        primary_key_in_index: bool = True,
                        ) -> pd.DataFrame:
        """ 从本地数据表中读取数据并返回DataFrame，不修改数据格式，primary_key为DataFrame的index

        在读取数据表时读取所有的列，但是返回值筛选ts_code以及trade_date between start 和 end

        Parameters
        ----------
        table: str
            数据表名称
        shares: str
            ts_code筛选条件，逗号分隔字符串，为空时给出所有记录
        start: str，
            YYYYMMDD格式日期，为空时不筛选
        end: str，
            YYYYMMDD格式日期，当start不为空时有效，筛选日期范围
        primary_key_in_index: bool, default True
            是否将primary key设置为DataFrame的index
            如果为False，primary key将作为普通的列返回，此时DataFrame的index为默认的整数index

        Returns
        -------
        pd.DataFrame 返回数据表中的数据

        """

        if not isinstance(table, str):
            err = TypeError(f'table name should be a string, got {type(table)} instead.')
            raise err
        if table not in TABLE_MASTERS.keys():
            raise KeyError(f'Invalid table name: {table}.')

        if shares is not None:
            if isinstance(shares, str):
                shares = str_to_list(shares)

        if (start is not None) and (end is not None):
            start = regulate_date_format(start)
            end = regulate_date_format(end)
            assert pd.to_datetime(start) <= pd.to_datetime(end)

        columns, dtypes, primary_key, pk_dtypes = get_built_in_table_schema(table)
        # 识别primary key中的证券代码列名和日期类型列名，确认是否需要筛选证券代码及日期
        share_like_pk = None
        date_like_pk = None
        if shares is not None:
            try:
                varchar_like_dtype = [item for item in pk_dtypes if item[:7] == 'varchar'][0]
                share_like_pk = primary_key[pk_dtypes.index(varchar_like_dtype)]
            except:
                msg = f'can not find share-like primary key in the table {table}!\n' \
                      f'passed argument shares will be ignored!'
                warnings.warn(msg, RuntimeWarning, stacklevel=2)
                share_like_pk = None
                shares = None
        # 识别Primary key中的日期型字段，并确认是否需要筛选日期型pk
        if (start is not None) and (end is not None) and ("month" in primary_key):
            # case 1: 识别到了month字段，且start和end都不为空
            date_like_pk = 'month'
            start = date_to_month_format(start)
            end = date_to_month_format(end)
        elif (start is not None) and (end is not None) and ("quarter" in primary_key):
            # case 2: 识别到了quarter字段，且start和end都不为空
            date_like_pk = 'quarter'
            start = date_to_quarter_format(start)
            end = date_to_quarter_format(end)
        elif (start is not None) and (end is not None):
            # case 3: 未识别到quarter或者month字段，根据字段类型检查是否有date-like字段
            try:
                date_like_dtype = [item for item in pk_dtypes if item in ['date', 'datetime']][0]
                date_like_pk = primary_key[pk_dtypes.index(date_like_dtype)]
            except Exception as e:
                msg = f'{e}\ncan not find date-like primary key in the table {table}!\n' \
                      f'passed start({start}) and end({end}) arguments will be ignored!'
                warnings.warn(msg, RuntimeWarning, stacklevel=2)
                date_like_pk = None
                start = None
                end = None

        if self.source_type == 'file':
            # 读取table数据, 从本地文件中读取的DataFrame已经设置好了primary_key index
            # 但是并未按shares和start/end进行筛选，需要手动筛选

            df = self._read_file(file_name=table,
                                 primary_key=primary_key,
                                 pk_dtypes=pk_dtypes,
                                 share_like_pk=share_like_pk,
                                 shares=shares,
                                 date_like_pk=date_like_pk,
                                 start=start,
                                 end=end)
            if df.empty:
                return df
            # TODO: 这里对所有读取的文件都进行筛选，需要考虑是否在read_table_data还需要筛选？
            #  也就是说，在read_table_data级别筛选数据还是在read_file/read_database级别
            #  筛选数据？目前看在read_file级别筛选即可，暂时注释掉这里的筛选代码，可以提高速度
            # if share_like_pk is not None:
            #     df = df.loc[df.index.isin(shares, level=share_like_pk)]
            # if date_like_pk is not None:
            #     # 两种方法实现筛选，分别是df.query 以及 df.index.get_level_values()
            #     # 第一种方法， df.query
            #     # df = df.query(f"{date_like_pk} >= {start} and {date_like_pk} <= {end}")
            #     # 第二种方法：df.index.get_level_values()
            #     m1 = df.index.get_level_values(date_like_pk) >= start
            #     m2 = df.index.get_level_values(date_like_pk) <= end
            #     df = df[m1 & m2]
        elif self.source_type == 'db':
            # TODO: 下面这部分代码应该都不需要，如果数据库表不存在时就新建一张表，则跟文件操作
            #  结果不一致，另外shares和start / end的判断跟前面重复了，且跟文件操作也不一样
            #  暂时先注释掉，后续再根据实际情况修改
            """
            if not self._db_table_exists(db_table=table):
                # 如果数据库中不存在该表，则创建表
                self._new_db_table(db_table=table, columns=columns, dtypes=dtypes, primary_key=primary_key)
            if share_like_pk is None:
                shares = None
            if date_like_pk is None:
                start = None
                end = None"""
            # 读取数据库表，从数据库表中读取的DataFrame并未设置primary_key index，因此
            # 需要手动设置index，但是读取的数据已经按shares/start/end筛选，无需手动筛选
            df = self._read_database(db_table=table,
                                     share_like_pk=share_like_pk,
                                     shares=shares,
                                     date_like_pk=date_like_pk,
                                     start=start,
                                     end=end)
            if df.empty:
                return df
            set_primary_key_index(df, primary_key, pk_dtypes)
        else:  # for unexpected cases:
            err = TypeError(f'Invalid value DataSource.source_type: {self.source_type}')
            raise err

        if not primary_key_in_index:
            df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtypes)

        return df

    def export_table_data(self, table, file_name=None, file_path=None, shares=None, start=None, end=None):
        """ 将数据表中的数据读取出来之后导出到一个文件中，便于用户使用过程中小规模转移数据或察看数据

        使用这个函数时，用户可以不用理会数据源的类型，只需要指定数据表名称，以及筛选条件即可
        导出的数据会被保存为csv文件，用户可以自行指定文件名以及文件存储路径，如果不指定文件名，
        则默认使用数据表名称作为文件名，如果不指定文件存储路径，则默认使用当前工作目录作为
        文件存储路径

        Parameters
        ----------
        table: str
            数据表名称
        file_name: str, optional
            导出的文件名，如果不指定，则默认使用数据表名称作为文件名
        file_path: str, optional
            导出的文件存储路径，如果不指定，则默认使用当前工作目录作为文件存储路径
        shares: list of str, optional
            ts_code筛选条件，为空时给出所有记录
        start: DateTime like, optional
            YYYYMMDD格式日期，为空时不筛选
        end: Datetime like，optional
            YYYYMMDD格式日期，当start不为空时有效，筛选日期范围

        Returns
        -------
        file_path_name: str
            导出的文件的完整路径
        """
        # TODO: Implement this function: export_table_data
        # 如果table不合法，则抛出异常
        table_master = get_table_master()
        non_sys_tables = table_master[table_master['table_usage'] != 'sys'].index.to_list()
        if table not in non_sys_tables:
            err = ValueError(f'Invalid table name: {table}!')
            raise err

        # 检查file_name是否合法
        if file_name is None:
            file_name = table
        if file_path is None:
            file_path = os.getcwd()
        # 检查file_path_name是否存在，如果已经存在，则抛出异常
        file_path_name = path.join(file_path, file_name)
        if os.path.exists(file_path_name):
            err = FileExistsError(f'File {file_path_name} already exists!')
            raise err

        # 读取table数据
        df = self.read_table_data(table=table, shares=shares, start=start, end=end)
        # 将数据写入文件
        try:
            df.to_csv(file_path_name, encoding='utf-8')
        except Exception as e:
            err = RuntimeError(f'{e}, Failed to export table {table} to file {file_path_name}!')
            raise err

        return file_path_name

    def write_table_data(self, df, table, on_duplicate='ignore'):
        """ 将df中的数据写入本地数据表(本地文件或数据库)

        如果本地数据表不存在则新建数据表，如果本地数据表已经存在，则将df数据添加在本地表中
        如果添加的数据主键与已有的数据相同，处理方式由on_duplicate参数确定

        Parameters
        ----------
        df: pd.DataFrame
            一个数据表，数据表的列名应该与本地数据表定义一致
        table: str
            本地数据表名，
        on_duplicate: str
            重复数据处理方式(仅当mode==db的时候有效)
            -ignore: 默认方式，将全部数据写入数据库表的末尾
            -update: 将数据写入数据库表中，如果遇到重复的pk则修改表中的内容

        Returns
        -------
        int: 写入的数据条数

        Notes
        -----
        注意！！不应直接使用该函数将数据写入本地数据库，因为写入的数据不会被检查
        请使用update_table_data()来更新或写入数据到本地
        """

        assert isinstance(df, pd.DataFrame)
        if not isinstance(table, str):
            err = TypeError(f'table name should be a string, got {type(table)} instead.')
            raise err
        if table not in TABLE_MASTERS.keys():
            raise KeyError(f'Invalid table name.')
        columns, dtypes, primary_key, pk_dtype = get_built_in_table_schema(table)
        rows_affected = 0
        df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtype)
        if self.source_type == 'file':
            set_primary_key_index(df, primary_key=primary_key, pk_dtypes=pk_dtype)
            rows_affected = self._write_file(df, file_name=table)
        elif self.source_type == 'db':
            if not self._db_table_exists(table):
                self._new_db_table(db_table=table, columns=columns, dtypes=dtypes, primary_key=primary_key)
            if on_duplicate == 'ignore':
                rows_affected = self._write_database(df, db_table=table, primary_key=primary_key)
            elif on_duplicate == 'update':
                rows_affected = self._update_database(df, db_table=table, primary_key=primary_key)
            else:  # for unexpected cases
                err = KeyError(f'Invalid process mode on duplication: {on_duplicate}')
                raise err
        self._table_list.add(table)
        return rows_affected

    def update_table_data(self, table, df, merge_type='update') -> int:
        """ 检查输入的df，去掉不符合要求的列或行后，将数据合并到table中，包括以下步骤：

            1，检查下载后的数据表的列名是否与数据表的定义相同，删除多余的列
            2，如果datasource type是"db"，删除下载数据中与本地数据重复的部分，仅保留新增数据
            3，如果datasource type是"file"，将下载的数据与本地数据合并并去重
            返回处理完毕的dataFrame

        Parameters
        ----------
        table: str,
            数据表名，必须是database中定义的数据表
        merge_type: str
            指定如何合并下载数据和本地数据：
            - 'update': 默认值，如果下载数据与本地数据重复，用下载数据替代本地数据
            - 'ignore' : 如果下载数据与本地数据重复，忽略重复部分
        df: pd.DataFrame
            通过传递一个DataFrame获取数据
            如果数据获取渠道为"df"，则必须给出此参数

        Returns
        -------
        int, 写入数据表中的数据的行数
        """
        if not isinstance(df, pd.DataFrame):
            err = TypeError(f'df should be a dataframe, got {type(df)} instead')
            raise err
        if not isinstance(merge_type, str):
            err = TypeError(f'merge type should be a string, got {type(merge_type)} instead.')
            raise err
        if merge_type not in ['ignore', 'update']:
            raise KeyError(f'Invalid merge type, should be either "ignore" or "update"')

        dnld_data = df
        if dnld_data.empty:
            return 0

        table_columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
        dnld_data = set_primary_key_frame(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
        dnld_columns = dnld_data.columns.to_list()
        # 如果table中的相当部分(25%)不能从df中找到，判断df与table完全不匹配，报错
        # 否则判断df基本与table匹配，根据Constraints，添加缺少的列(通常为NULL列)
        missing_columns = [col for col in table_columns if col not in dnld_columns]
        if len(missing_columns) >= (len(table_columns) * 0.75):
            err = ValueError(f'there are too many missing columns in downloaded df, can not merge to local table:'
                             f'table_columns:\n{[table_columns]}\n'
                             f'downloaded:\n{[dnld_columns]}')
            raise err
        else:
            pass  # 在后面调整列顺序时会同时添加缺的列并调整顺序
        # 删除数据中过多的列，不允许出现缺少列
        columns_to_drop = [col for col in dnld_columns if col not in table_columns]
        if len(columns_to_drop) > 0:
            dnld_data.drop(columns=columns_to_drop, inplace=True)
        # 确保df与table的column顺序一致
        if len(missing_columns) > 0 or any(item_d != item_t for item_d, item_t in zip(dnld_columns, table_columns)):
            dnld_data = dnld_data.reindex(columns=table_columns, copy=False)
        if self.source_type == 'file':
            # 如果source_type == 'file'，需要将下载的数据与本地数据合并，本地数据必须全部下载，
            # 数据量大后非常费时
            # 因此本地文件系统承载的数据量非常有限
            local_data = self.read_table_data(table)
            set_primary_key_index(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
            # 根据merge_type处理重叠部分：
            if merge_type == 'ignore':
                # 丢弃下载数据中的重叠部分
                dnld_data = dnld_data[~dnld_data.index.isin(local_data.index)]
            elif merge_type == 'update':  # 用下载数据中的重叠部分覆盖本地数据，下载数据不变，丢弃本地数据中的重叠部分(仅用于本地文件保存的情况)
                local_data = local_data[~local_data.index.isin(dnld_data.index)]
            else:  # for unexpected cases
                raise KeyError(f'Invalid merge type, got "{merge_type}"')
            rows_affected = self.write_table_data(pd.concat([local_data, dnld_data]), table=table)
        elif self.source_type == 'db':
            rows_affected = self.write_table_data(df=dnld_data, table=table, on_duplicate=merge_type)
        else:  # unexpected case
            raise KeyError(f'invalid data source type: {self.source_type}')

        return rows_affected

    def drop_table_data(self, table):
        """ 删除本地存储的数据表(操作不可撤销，谨慎使用)
        如果数据源设置了allow_drop_table为False，则无法删除数据表并报错

        Parameters
        ----------
        table: str,
            本地数据表的名称

        Returns
        -------
        None

        Raises
        ------
        RuntimeError: 当数据源设置了allow_drop_table为False时，无法删除数据表并报错
        """

        if not self.allow_drop_table:
            err = RuntimeError('Can\'t drop table from current datasource according to setting, please check: '
                               'datasource.allow_drop_table')
            raise err

        if self.source_type == 'db':
            self._drop_db_table(db_table=table)
        elif self.source_type == 'file':
            self._drop_file(file_name=table)
        self._table_list.difference_update([table])
        return None

    def get_table_data_coverage(self, table, column, min_max_only=False):
        """ 获取本地数据表内容的覆盖范围，取出数据表的"column"列中的去重值并返回

        Parameters
        ----------
        table: str,
            数据表的名称
        column: str or list of str
            需要去重并返回的数据列
        min_max_only: bool, default False
            为True时不需要返回整个数据列，仅返回最大值和最小值
            如果仅返回最大值和和最小值，返回值为一个包含两个元素的列表，
            第一个元素是最小值，第二个是最大值，第三个是总数量

        Returns
        -------
        List, 代表数据覆盖范围的列表

        Examples
        --------
        >>> import qteasy
        >>> qteasy.QT_DATA_SOURCE.get_table_data_coverage('stock_daily', 'ts_code')
        Out:
        ['000001.SZ',
         '000002.SZ',
         '000003.SZ',
         '000004.SZ',
         '000005.SZ',
         '000006.SZ',
         ...,
         '002407.SZ',
         '002408.SZ',
         '002409.SZ',
         '002410.SZ',
         '002411.SZ',
         ...]
        >>> import qteasy as qt
        >>> qt.QT_DATA_SOURCE.get_table_data_coverage('stock_daily', 'ts_code', min_max_only=True)
        Out:
        ['000001.SZ', '873593.BJ']
        """
        if self.source_type == 'db':
            if min_max_only:
                return self._get_db_table_minmax(table, column)
            else:
                return self._get_db_table_coverage(table, column)
        elif self.source_type == 'file':
            columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
            return self._get_file_table_coverage(table, column, primary_keys, pk_dtypes, min_max_only)
        else:
            err = TypeError(f'Invalid source type: {self.source_type}')
        raise err

    def get_data_table_size(self, table, human=True, string_form=True):
        """ 获取数据表占用磁盘空间的大小

        Parameters
        ----------
        table: str
            数据表名称
        human: bool, default True
            True时显示容易阅读的形式，如1.5MB而不是1590868， False时返回字节数
        string_form: bool, default True
            True时以字符串形式返回结果，便于打印

        Returns
        -------
        tuple (size, rows): tuple of int or str:

        """
        if self.source_type == 'file':
            size = self._get_file_size(table)
            rows = self._get_file_rows(table)
            # rows = 'unknown'
        elif self.source_type == 'db':
            rows, size = self._get_db_table_size(table)
        else:
            err = RuntimeError(f'unknown source type: {self.source_type}')
            raise err
        if size == -1:
            return 0, 0
        if not string_form:
            return size, rows
        if human:
            return f'{human_file_size(size)}', f'{human_units(rows)}'
        else:
            return f'{size}', f'{rows}'

    def get_table_info(self, table, verbose=True, print_info=True, human=True) -> dict:
        """ 获取并打印数据表的相关信息，包括数据表是否已有数据，数据量大小，占用磁盘空间、数据覆盖范围，
            以及数据下载方法

        Parameters:
        -----------
        table: str
            数据表名称
        verbose: bool, Default: True
            是否显示更多信息，如是，显示表结构等信息
        print_info: bool, Default: True
            是否打印输出所有结果
        human: bool, Default: True
            是否给出容易阅读的字符串形式

        Returns
        -------
        一个dict，包含数据表的结构化信息：
        {
            table name:    1, str, 数据表名称
            table_exists:  2, bool，数据表是否存在
            table_size:    3, int/str，数据表占用磁盘空间，human 为True时返回容易阅读的字符串
            table_rows:    4, int/str，数据表的行数，human 为True时返回容易阅读的字符串
            primary_key1:  5, str，数据表第一个主键名称
            pk_count1:     6, int，数据表第一个主键记录数量
            pk_min1:       7, obj，数据表主键1起始记录
            pk_max1:       8, obj，数据表主键2最终记录
            primary_key2:  9, str，数据表第二个主键名称
            pk_count2:     10, int，数据表第二个主键记录
            pk_min2:       11, obj，数据表主键2起始记录
            pk_max2:       12, obj，数据表主键2最终记录
        }
        """
        pk1 = None
        pk_records1 = None
        pk_min1 = None
        pk_max1 = None
        pk2 = None
        pk_records2 = None
        pk_min2 = None
        pk_max2 = None
        if not isinstance(table, str):
            err = TypeError(f'table should be name of a table, got {type(table)} instead')
            raise err
        if table not in TABLE_MASTERS:
            err = ValueError(f'in valid table name: {table}')
            raise err

        columns, dtypes, remarks, primary_keys, pk_dtypes = get_built_in_table_schema(table,
                                                                                      with_remark=True,
                                                                                      with_primary_keys=True)
        table_desc = TABLE_MASTERS[table][1]
        critical_key = TABLE_MASTERS[table][6]
        table_schema = pd.DataFrame({'columns': columns,
                                     'dtypes':  dtypes,
                                     'remarks': remarks})
        table_exists = self.table_data_exists(table)
        if print_info:
            if table_exists:
                table_size, table_rows = self.get_data_table_size(table, human=human)
            else:
                table_size, table_rows = '0 MB', '0'
            print(f'<{table}>--<{table_desc}>\n{table_size}/{table_rows} records on disc\n'
                  f'primary keys: \n'
                  f'----------------------------------------')
        else:
            if table_exists:
                table_size, table_rows = self.get_data_table_size(table, string_form=human, human=human)
            else:
                table_size, table_rows = 0, 0
        pk_count = 0
        for pk in primary_keys:
            pk_min_max_count = self.get_table_data_coverage(table, pk, min_max_only=True)
            pk_count += 1
            critical = ''
            record_count = 'unknown'

            if len(pk_min_max_count) == 3:
                record_count = pk_min_max_count[2]
            if len(pk_min_max_count) == 0:
                pk_min_max_count = ['N/A', 'N/A']
            if print_info:
                critical = "*" if pk == critical_key else " "
                print(f'{pk_count}: {critical} {pk}:  <{record_count}> entries\n'
                      f'     starts:'
                      f' {pk_min_max_count[0]}, end: {pk_min_max_count[1]}')
            if pk_count == 1:
                pk1 = pk
                pk_records1 = record_count
                pk_min1 = pk_min_max_count[0]
                pk_max1 = pk_min_max_count[1]
            elif pk_count == 2:
                pk2 = pk
                pk_records2 = record_count
                pk_min2 = pk_min_max_count[0]
                pk_max2 = pk_min_max_count[1]
            else:
                pass
        if verbose and print_info:
            print(f'\ncolumns of table:\n'
                  f'------------------------------------\n'
                  f'{table_schema}\n')
        _res = {'table':        table,
                'table_exists': table_exists,
                'table_size':   table_size,
                'table_rows':   table_rows,
                'primary_key1': pk1,
                'pk_records1':  pk_records1,
                'pk_min1':      pk_min1,
                'pk_max1':      pk_max1,
                'primary_key2': pk2,
                'pk_records2':  pk_records2,
                'pk_min2':      pk_min2,
                'pk_max2':      pk_max2
                }
        return _res

    # ==============
    # 系统操作表操作函数，专门用于操作sys_operations表，记录系统操作信息，数据格式简化
    # ==============
    def get_sys_table_last_id(self, table):
        """ 从已有的table中获取最后一个id

        Parameters
        ----------
        table: str
            数据表名称

        Returns
        -------
        last_id: int 当前使用的最后一个ID（自增ID）
        """

        from .datatables import ensure_sys_table
        ensure_sys_table(table)
        # 如果是文件系统，在可行的情况下，直接从文件系统中获取最后一个id，否则读取文件数据后获取id
        if self.source_type in ['file']:
            df = self.read_sys_table_data(table)
            if df.empty:
                return 0
            return int(df.index.max())
        # 如果是数据库系统，直接获取最后一个id, 这种做法某些情况下有问，使用下面的方法无法获取最后一个id
        elif self.source_type == 'db':
            if not self._db_table_exists(table):
                columns, dtypes, prime_keys, pk_dtypes = get_built_in_table_schema(table)
                self._new_db_table(table,
                                   columns=columns,
                                   dtypes=dtypes,
                                   primary_key=prime_keys,
                                   auto_increment_id=True)
                return 0

            columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table, with_primary_keys=True)
            primary_key = primary_keys[0]
            sql = f"SELECT * FROM `{table}` ORDER BY `{primary_key}` DESC LIMIT 1;"
            res = self._db_execute_one(sql)
            if res is not None:
                return res[0][0] if len(res) > 0 else 0

        else:  # for other unexpected cases
            pass
        pass

    def read_sys_table_data(self, table, **kwargs) -> pd.DataFrame:
        """读取系统操作表的数据，包括读取所有记录，以及根据给定的条件读取记录

        返回的数据类型为pd.DataFrame，如果给出kwargs，返回根据条件筛选后的数据

        Parameters
        ----------
        table: str
            需要读取的数据表名称
        kwargs: dict
            筛选数据的条件，包括用作筛选条件的字典如: {account_id = 123}

        Returns
        -------
        pd.DataFrame:
            返回的数据为DataFrame，如果给出kwargs，返回的数据仅包括筛选后的数据
        """

        from .datatables import ensure_sys_table
        ensure_sys_table(table)

        # 检查kwargs中是否有不可用的字段
        columns, dtypes, p_keys, pk_dtypes = get_built_in_table_schema(table)
        if any(k not in columns for k in kwargs):
            err = KeyError(f'kwargs not valid: {[k for k in kwargs if k not in columns]}')
            raise err

        # 读取数据，如果给出id，则只读取一条数据，否则读取所有数据
        if self.source_type == 'db':
            res_df = self._read_database(table)
            if res_df.empty:
                return res_df
            set_primary_key_index(res_df, primary_key=p_keys, pk_dtypes=pk_dtypes)
        elif self.source_type == 'file':
            res_df = self._read_file(table, p_keys, pk_dtypes)
        else:  # for other unexpected cases
            return pd.DataFrame()

        if res_df.empty:
            return res_df

        # 筛选数据
        for k, v in kwargs.items():
            res_df = res_df.loc[res_df[k] == v]

        return res_df.sort_index()

    def read_sys_table_record(self, table, *, record_id: int, **kwargs) -> dict:
        """ 读取系统操作表的数据，根据指定的id读取数据，返回一个dict

        本函数调用read_sys_table_data()读取整个数据表，并返回record_id行的数据
        返回的dict包含所有字段的值，key为字段名，value为字段值

        Parameters
        ----------
        table: str
            需要读取的数据表名称
        record_id: int
            需要读取的数据的id
        kwargs: dict
            筛选数据的条件，包括用作筛选条件的字典如: account_id = 123

        Returns
        -------
        data: dict
            读取的数据，包括数据表的结构化信息以及数据表中的记录
        """

        # 检查record_id是否合法
        if record_id is not None and record_id <= 0:
            return {}

        data = self.read_sys_table_data(table, **kwargs)
        if data.empty:
            return {}

        if record_id not in data.index:
            return {}

        return data.loc[record_id].to_dict()

    def update_sys_table_data(self, table: str, record_id: int, **data) -> int:
        """ 更新系统操作表的数据，根据指定的id更新数据，更新的内容由kwargs给出。

        每次只能更新一条数据，数据以dict形式给出
        可以更新一个或多个字段，如果给出的字段不存在，则抛出异，id不可更新。
        id必须存在，否则抛出异常

        Parameters
        ----------
        table: str
            需要更新的数据表名称
        record_id: int
            需要更新的数据的id
        data: dict
            需要更新的数据，包括需要更新的字段如: account_id = 123

        Returns
        -------
        id: int
            更新的记录ID

        Raises
        ------
        KeyError: 当给出的id不存在或为None时
        KeyError: 当给出的字段不存在时
        """

        from .datatables import ensure_sys_table
        ensure_sys_table(table)
        # TODO: 为了提高开发速度，使用self.update_table_data()，后续需要重构代码
        #  用下面的思路重构代码，提高运行效率
        """
        # 检察数据，如果**kwargs中有不可用的字段，则抛出异常，如果kwargs为空，则返回None

        # 判断id是否存在范围内，如果id超出范围，则抛出异常

        # 写入数据，如果是文件系统，读取文件，更新数据，然后写入文件，如果是数据库，直接用SQL更新数据库
        if self.source_type == 'file':
            pass
        elif self.source_type == 'db':
            pass
        else: # for other unexpected cases
            pass
        pass
        """

        # 将data构造为一个df，然后调用self.update_table_data()
        table_data = self.read_sys_table_record(table, record_id=record_id)
        if table_data == {}:
            raise KeyError(f'record_id({record_id}) not found in table {table}')

        # 当data中有不可用的字段时，会抛出异常
        columns, dtypes, p_keys, pk_dtypes = get_built_in_table_schema(table)
        data_columns = [col for col in columns if col not in p_keys]
        if any(k not in data_columns for k in data.keys()):
            raise KeyError(f'kwargs not valid: {[k for k in data.keys() if k not in data_columns]}')

        # 更新original_data
        table_data.update(data)

        df_data = pd.DataFrame(table_data, index=[record_id])
        df_data.index.name = p_keys[0]
        self.update_table_data(table, df_data, merge_type='update')
        return record_id

    def insert_sys_table_data(self, table: str, **data) -> int:
        """ 插入系统操作表的数据

        一次插入一条记录，数据以dict形式给出
        不需要给出数据的ID，因为ID会自动生成
        如果给出的数据字段不完整，则抛出异常
        如果给出的数据中有不可用的字段，则抛出异常

        Parameters
        ----------
        table: str
            需要更新的数据表名称
        data: dict
            需要更新或插入的数据，数据的key必须与数据库表的字段相同，否则会抛出异常

        Returns
        -------
        record_id: int
            更新的记录ID

        Raises
        ------
        KeyError: 当给出的字段不完整或者有不可用的字段时
        """

        from .datatables import ensure_sys_table
        ensure_sys_table(table)
        # TODO: 为了缩短开发时间，先暂时调用self.update_table_data()，后续需要重构
        #  按照下面的思路重构简化代码：
        """
        # 检察数据，如果data中有不可用的字段，则抛出异常，如果data为空，则返回None
        if not isinstance(data, dict):
            err = TypeError(f'Input data must be a dict, but got {type(data)}')
            raise err
        if not data:
            return None

        columns, dtypes, p_keys, pk_dtypes = get_built_in_table_schema(table)
        values = list(data.values())
        # 检查data的key是否与column完全一致，如果不一致，则抛出异常
        if list(data.keys() != columns):
            raise KeyError(f'Input data keys must be the same as the table columns, '
                           f'got {list(data.keys())} vs {columns}')

        # 写入数据，如果是文件系统，对可行的文件类型直接写入文件，否则读取文件，插入数据后再写入文件，如果是数据库，直接用SQL更新数据库
        if self.source_type == 'file':
            # 获取最后一个ID，然后+1，作为新的ID(仅当source_type==file时，数据库可以自动生成ID)
            last_id = self.get_last_id(table)
            new_id = last_id + 1 if last_id is not None else 1
            pass
        elif self.source_type == 'db':
            # 使用SQL插入一条数据到数据库
            db_table = table
            if not self._db_table_exists(db_table=table):
                # 如果数据库中不存在该表，则创建表
                self._new_db_table(db_table=table, columns=columns, dtypes=dtypes, primary_key=primary_key)
            # 生成sql语句
            sql = f"INSERT INTO `{db_table}` ("
            for col in columns[:-1]:
                sql += f"`{col}`, "
            sql += f"`{columns[-1]}`)\nVALUES\n("
            for val in values[:-1]:
                sql += f"{val}, "
            sql += f"{values[-1]})\n"
            try:
                self.conn.execute(sql)
                self.conn.commit()
            except Exception as e:
                err = RuntimeError(f'{e}, An error occurred when insert data into table {table} with sql:\n{sql}')
                raise err
        else:  # for other unexpected cases
            pass
        last_id = self.get_last_id(table)
        return last_id
        """

        # 将data构造为一个df，然后调用self.update_table_data()
        last_id = self.get_sys_table_last_id(table)
        record_id = last_id + 1 if last_id is not None else 1
        columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
        data_columns = [col for col in columns if col not in primary_keys]
        # 检查data的key是否与data_column完全一致，如果不一致，则抛出异常
        if any(k not in data_columns for k in data.keys()) or any(k not in data.keys() for k in data_columns):
            err = KeyError(f'Input data keys must be the same as the table data columns, '
                           f'got {list(data.keys())} vs {data_columns}')
            raise err
        df = pd.DataFrame(data, index=[record_id], columns=data.keys())
        df = df.reindex(columns=columns)
        df.index.name = primary_keys[0]

        # 插入数据
        self.update_table_data(table, df, merge_type='ignore')
        # TODO: 这里为什么要用'ignore'而不是'update'? 现在改为'update'，
        #  test_database和test_trading测试都能通过，后续完整测试
        return record_id

    def delete_sys_table_data(self, table: str, record_ids: (list, tuple)) -> int:
        """ 删除系统数据表中的某些记录，被删除的记录的ID使用列表或tuple传入

        parameters
        ----------
        table: str
            需要删除数据的表名
        record_ids: list of int or tuple of int
            需要删除的记录的ID列表

        Returns
        -------
        int
            删除的记录数量
        """

        from .datatables import ensure_sys_table
        # 如果不是system table，直接返回0
        try:
            ensure_sys_table(table)
        except KeyError:
            f'{table} is not valid table, can not delete records from it.'
            return 0
        except TypeError:
            f'{table} is not a system table, can not delete records from it.'
            return 0
        except Exception as e:
            f'An error occurred when checking table {table}: {e}'
            return 0

        # 检查record_ids是否合法
        if not isinstance(record_ids, (list, tuple)):
            err = TypeError(f'record_ids should be a list or tuple, got {type(record_ids)} instead')
            raise err
        if not all(isinstance(rid, int) for rid in record_ids):
            err = TypeError(f'all record_ids should be int, got {[type(rid) for rid in record_ids]} instead')
            raise err

        columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table, with_primary_keys=True)
        primary_key = primary_keys[0]

        if self.source_type == 'db':
            res = self._delete_database_records(table, primary_key=primary_key, record_ids=record_ids)
        elif self.source_type == 'file':
            res = self._delete_file_records(table, primary_key=primary_key, record_ids=record_ids)
        else:
            err = RuntimeError(f'invalid source type: {self.source_type}')
            raise err

        return res

    # ==============
    # 特殊函数，一些有用的API
    # ==============
    def get_all_basic_table_data(self, refresh_cache=False, raise_error=True):
        """ 一个快速获取所有basic数据表的函数，通常情况缓存处理以加快速度
        如果设置refresh_cache为True，则清空缓存并重新下载数据

        Parameters
        ----------
        refresh_cache: Bool, Default False
            如果为True，则清空缓存并重新下载数据
        raise_error: Bool, Default True
            如果为True，则在数据表为空时抛出ValueError

        Returns
        -------
        DataFrame
        """

        if refresh_cache:
            self._get_all_basic_table_data.cache_clear()
        return self._get_all_basic_table_data(raise_error=raise_error)

    @lru_cache(maxsize=1)
    def _get_all_basic_table_data(self, raise_error=True):
        """ 获取所有basic数据表

        Parameters
        ----------
        raise_error: Bool, Default True
            如果为True，则在数据表为空时抛出ValueError

        Returns
        -------
        tuple of DataFrames:
        df_s: stock_basic
        df_i: index_basic
        df_f: fund_basic
        df_ft: future_basic
        df_o: opt_basic

        Raises
        ------
        ValueError
            如果任意一个数据表为空，则抛出ValueError
        """
        df_s = self.read_table_data('stock_basic')
        if df_s.empty and raise_error:
            err = ValueError('stock_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="stock_basic")"')
            raise err
        df_i = self.read_table_data('index_basic')
        if df_i.empty and raise_error:
            err = ValueError('index_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="index_basic")"')
            raise err
        df_f = self.read_table_data('fund_basic')
        if df_f.empty and raise_error:
            err = ValueError('fund_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="fund_basic")"')
            raise err
        df_ft = self.read_table_data('future_basic')
        if df_ft.empty and raise_error:
            err = ValueError('future_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="future_basic")"')
            raise err
        df_o = self.read_table_data('opt_basic')
        if df_o.empty and raise_error:
            err = ValueError('opt_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="opt_basic")"')
            raise err
        df_ths = self.read_table_data('ths_index_basic')
        if df_ths.empty and raise_error:
            err = ValueError('ths_index_basic table is empty, please refill data source with '
                             '"qt.refill_data_source(tables="ths_index_basic")"')
            raise err
        return df_s, df_i, df_f, df_ft, df_o, df_ths

    def drop_empty_tables(self) -> int:
        """ 从datasource中删除所有空表，即行数为0的表

        Returns
        -------
        int
            删除的表数量
        """

        dropped_count = 0

        for table in self.all_tables:
            table_info = self.get_table_info(table, print_info=False)
            table_rows = table_info['table_rows']
            if table_rows == 0:
                self.drop_table_data(table)
                dropped_count += 1

        return dropped_count

    # TODO: 在新的架构下，似乎不再需要这个函数，可以考虑删除
    def reconnect(self):
        """ 当数据库超时或其他原因丢失连接时，Ping数据库检查状态，
            如果可行的话，重新连接数据库

        Returns
        -------
        True: 连接成功
        False: 连接失败
        """
        if self.source_type != 'db':
            return True
        pass
