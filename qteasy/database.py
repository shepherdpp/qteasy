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

from concurrent.futures import as_completed, ThreadPoolExecutor
from functools import lru_cache

from .datatypes import (
    DATA_TYPE_MAP,
    DATA_TYPE_MAP_COLUMNS,
    DATA_TYPE_MAP_INDEX_NAMES,
)

from .datatables import (
    AVAILABLE_CHANNELS,
    AVAILABLE_DATA_FILE_TYPES,
    TABLE_MASTERS,
    TABLE_SCHEMA,
    TABLE_MASTER_COLUMNS,
    TABLE_USAGES,
    ADJUSTABLE_PRICE_TYPES,
    DataConflictWarning
)

from .utilfuncs import (
    progress_bar,
    sec_to_duration,
    nearest_market_trade_day,
    input_to_list,
    is_market_trade_day,
    str_to_list,
    regulate_date_format,
    freq_dither,
    pandas_freq_alias_version_conversion,
    _wildcard_match,
    _partial_lev_ratio,
    _lev_ratio,
    human_file_size,
    human_units,
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
    read_table_data(self, table, shares=None, start=None, end=None)
        从本地数据表中读取数据并返回DataFrame，不修改数据格式
    export_table_data(self, table, shares=None, start=None, end=None)
        NotImplemented 将数据表中的数据读取出来之后导出到一个文件中，便于用户使用过程中小
        规模转移数据
    get_history_data(self, shares, htypes, start, end, freq, asset_type='any', adj='none')
        根据给出的参数从不同的本地数据表中获取数据，并打包成一系列的DataFrame，以便组装成
        HistoryPanel对象。
    get_index_weights(self, index, start=None, end=None, shares=None)
        从本地数据仓库中获取一个指数的成分权重
    refill_local_source(self, tables=None, dtypes=None, freqs=None, asset_types=None,...)
        批量补充本地数据，手动或自动运行补充本地数据库

    """

    def __init__(self,
                 source_type: str = 'file',
                 file_type: str = 'csv',
                 file_loc: str = 'data/',
                 host: str = 'localhost',
                 port: int = 3306,
                 user: str = None,
                 password: str = None,
                 db_name: str = 'qt_db'):
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
            # optional packages to be imported
            try:
                import pymysql
            except ImportError:
                err = ImportError(f'Missing package \'pymysql\' for datasource type \'database\'. '
                                  f'Use pip or conda to install pymysql: $ pip install pymysql')
                raise err
            # set up connection to the data base
            if not isinstance(port, int):
                err = TypeError(f'port should be int type, got {type(port)} instead!')
                raise err
            if user is None:
                err = ValueError(f'Missing user name for database connection')
                raise err
            if password is None:
                err = ValueError(f'Missing password for database connection')
                raise err
            # try to create pymysql connections
            self.source_type = 'db'
            try:
                con = pymysql.connect(host=host,
                                      port=port,
                                      user=user,
                                      password=password)
                # 检查db是否存在，当db不存在时创建新的db
                cursor = con.cursor()
                sql = f"CREATE DATABASE IF NOT EXISTS {db_name}"
                cursor.execute(sql)
                con.commit()
                sql = f"USE {db_name}"
                cursor.execute(sql)
                con.commit()
                # create mysql database connection info
                self.connection_type = f'db:mysql://{host}@{port}/{db_name}'
                self.host = host
                self.port = port
                self.db_name = db_name
                self.file_type = None
                self.file_path = None
                self.__user__ = user
                self.__password__ = password

                con.close()

            except Exception as e:
                msg = f'Mysql connection failed: {str(e)}\n' \
                      f'Can not set data source type to "db", will fall back to csv file'

                warnings.warn(msg, RuntimeWarning)
                source_type = 'file'
                file_type = 'csv'
            finally:
                pass

        if source_type.lower() == 'file':
            # set up file type and file location
            if not isinstance(file_type, str):
                msg = f'file type should be a string, got {type(file_type)} instead!'
                err = TypeError(msg)
                raise err
            file_type = file_type.lower()
            if file_type not in AVAILABLE_DATA_FILE_TYPES:
                msg = f'file type not recognized, supported file types are {AVAILABLE_DATA_FILE_TYPES}'
                raise KeyError(msg)
            if file_type in ['hdf']:
                try:
                    import tables
                except ImportError:
                    err = ImportError(f'Missing optional dependency \'pytables\' for datasource file type '
                                      f'\'hdf\'. Please install pytables: $ conda install pytables')
                    raise err
                file_type = 'hdf'
            if file_type in ['feather', 'fth']:
                try:
                    import pyarrow
                except ImportError:
                    err = ImportError(f'Missing optional dependency \'pyarrow\' for datasource file type '
                                      f'\'feather\'. Use pip or conda to install pyarrow: $ pip install pyarrow')
                    raise err
                file_type = 'fth'
            from qteasy import QT_ROOT_PATH
            self.file_path = path.join(QT_ROOT_PATH, file_loc)
            try:
                os.makedirs(self.file_path, exist_ok=True)  # 确保数据dir不存在时创建一个
            except Exception:
                err = SystemError(f'Failed creating data directory \'{file_loc}\' in qt root path, '
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

    @property
    def tables(self) -> list:
        """ 所有已经建立的tables的清单"""
        return list(self._table_list)

    @property
    def all_tables(self) -> list:
        """ 获取所有数据表的清单"""
        return get_table_master().index.to_list()

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
        raise NotImplementedError

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

        # TODO: 这里对所有读取的文件都进行筛选，需要考虑是否在read_table_data还需要筛选？
        #  也就是说，在read_table_data级别筛选数据还是在read_file/read_database级别
        #  筛选数据？
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

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
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
        try:
            cursor = con.cursor()
            cursor.execute(sql)
            con.commit()

            data = cursor.fetchall()
            # return data in forms of DataFrame with correct column names
            df = pd.DataFrame(data, columns=[i[0] for i in cursor.description])

            return df
        except Exception as e:
            err = RuntimeError(f'{e}, error in reading data from database with sql:\n"{sql}"')
            raise err
        finally:
            con.close()

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
            dtype_mapping = {'object': 'varchar(255)',
                             'datetime64[ns]': 'datetime',
                             'int64': 'int',
                             'float32': 'float',
                             'float64': 'double',
                             }
            columns = df.columns
            dtypes = df.dtypes.tolist()
            dtypes = [dtype_mapping.get(str(dtype.name), 'varchar(255)') for dtype in dtypes]

            sql = f"CREATE TABLE IF NOT EXISTS `{db_table}` (\n"
            fields = []
            for col, dtype in zip(columns, dtypes):
                fields.append(f"`{col}` {dtype}\n")
            sql += f"{', '.join(fields)});"
            try:
                import pymysql
                con = pymysql.connect(
                        host=self.host,
                        port=self.port,
                        user=self.__user__,
                        password=self.__password__,
                        db=self.db_name,
                )
                cursor = con.cursor()
                cursor.execute(sql)
                con.commit()
            except Exception as e:
                con.rollback()
                err = RuntimeError(f'db table {db_table} does not exist and can not be created:\n'
                                   f'Exception:\n{e}\n'
                                   f'SQL:\n{sql}')
                raise err

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
        try:
            import pymysql
            con = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.__user__,
                    password=self.__password__,
                    db=self.db_name,
            )
            cursor = con.cursor()
            rows_affected = cursor.executemany(sql, df_tuple)
            con.commit()
            return rows_affected
        except Exception as e:
            con.rollback()
            err = RuntimeError(f'Error during inserting data to table {db_table} with following sql:\n'
                               f'Exception:\n{e}\n'
                               f'SQL:\n{sql} \nwith parameters (first 10 shown):\n{df_tuple[:10]}')
            raise err
        finally:
            con.close()

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

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        try:
            cursor = con.cursor()
            rows_affected = cursor.executemany(sql, df_tuple)
            con.commit()
            return rows_affected
        except Exception as e:
            con.rollback()
            err = RuntimeError(f'Error during updating data to table {db_table} with following sql:\n'
                               f'Exception:\n{e}\n'
                               f'SQL:\n{sql} \nwith parameters (first 10 shown):\n{df_tuple[:10]}')
            raise err
        finally:
            con.close()

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

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        try:
            cursor = con.cursor()
            rows_affected = cursor.execute(sql)
            con.commit()
            return rows_affected
        except Exception as e:
            con.rollback()
            err = RuntimeError(f'Error during deleting data from table {db_table} with following sql:\n'
                               f'Exception:\n{e}\n'
                               f'SQL:\n{sql}')
            raise err

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
        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        try:
            cursor.execute(sql)
            con.commit()
            res = [item[0] for item in cursor.fetchall()]
            if isinstance(res[0], datetime.datetime):
                res = list(pd.to_datetime(res).strftime('%Y%m%d'))
            return res
        except Exception as e:
            con.rollback()
            err = RuntimeError(f'Exception:\n{e}\n'
                               f'Error during querying data from db_table {db_table} with following sql:\n'
                               f'SQL:\n{sql} \n')
            raise err
        finally:
            con.close()

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
        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        try:
            cursor.execute(sql)
            con.commit()

            res = list(cursor.fetchall()[0])
            if isinstance(res[0], datetime.datetime):
                res = list(pd.to_datetime(res).strftime('%Y%m%d'))
            return res
        except Exception as e:
            con.rollback()
            err = RuntimeError(f'Exception:\n{e}\n'
                               f'Error during querying data from db_table {db_table} with following sql:\n'
                               f'SQL:\n{sql} \n')
            raise err
        finally:
            con.close()

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
        if self.source_type == 'file':
            err = RuntimeError('can not connect to database while source type is "file"')
            raise err
        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        sql = f"SHOW TABLES LIKE '{db_table}'"
        try:
            cursor.execute(sql)
            con.commit()
            res = cursor.fetchall()
            return len(res) > 0
        except Exception as e:
            err = RuntimeError(f'Exception:\n{e}\n'
                               f'Error during querying data from db_table {db_table} with following sql:\n'
                               f'SQL:\n{sql} \n')
            raise err
        finally:
            con.close()

    def _new_db_table(self, db_table, columns, dtypes, primary_key, auto_increment_id=False):
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

        Returns
        -------
        None
        """
        if self.source_type != 'db':
            err = TypeError(f'Datasource is not connected to a database')
            raise err

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
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
        sql += '\n);'
        try:
            cursor.execute(sql)
            con.commit()
        except Exception as e:
            con.rollback()
            print(f'error encountered during executing sql: \n{sql}\n error codes: \n{e}')
        finally:
            con.close()

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

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()

        sql = f"SELECT COLUMN_NAME, DATA_TYPE " \
              f"FROM INFORMATION_SCHEMA.COLUMNS " \
              f"WHERE TABLE_SCHEMA = Database() " \
              f"AND table_name = '{db_table}'" \
              f"ORDER BY ordinal_position;"
        try:
            cursor.execute(sql)
            con.commit()
            results = cursor.fetchall()
            # 为了方便，将cur_columns和new_columns分别包装成一个字典
            columns = {}
            for col, typ in results:
                columns[col] = typ
            return columns
        except Exception as e:
            con.rollback()
            print(f'error encountered during executing sql: \n{sql}\n error codes: \n{e}')
        finally:
            con.close()

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
        if self.source_type != 'db':
            err = TypeError(f'Datasource is not connected to a database')
            raise err
        if not isinstance(db_table, str):
            err = TypeError(f'db_table name should be a string, got {type(db_table)} instead')
            raise err

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        sql = f"DROP TABLE IF EXISTS {db_table};"
        try:
            cursor.execute(sql)
            con.commit()
        except Exception as e:
            con.rollback()
            print(f'error encountered during executing sql: \n{sql}\n error codes: \n{e}')
        finally:
            con.close()

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

        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        cursor = con.cursor()
        sql = "SELECT table_rows, data_length + index_length " \
              "FROM INFORMATION_SCHEMA.tables " \
              "WHERE table_schema = %s " \
              "AND table_name = %s;"
        try:
            cursor.execute(sql, (self.db_name, db_table))
            con.commit()
            rows, size = cursor.fetchall()[0]
            return rows, size
        except Exception as e:
            con.rollback()
            print(f'error encountered during executing sql: \n{sql}\n error codes: \n{e}')
        finally:
            con.close()

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

    def read_table_data(self, table, shares=None, start=None, end=None):
        """ 从本地数据表中读取数据并返回DataFrame，不修改数据格式

        在读取数据表时读取所有的列，但是返回值筛选ts_code以及trade_date between start 和 end

        Parameters
        ----------
        table: str
            数据表名称
        shares: list，
            ts_code筛选条件，为空时给出所有记录
        start: str，
            YYYYMMDD格式日期，为空时不筛选
        end: str，
            YYYYMMDD格式日期，当start不为空时有效，筛选日期范围

        Returns
        -------
        pd.DataFrame 返回数据表中的数据

        """

        # TODO: 历史数据表的规模较大，如果数据存储在数据库中，读取和存储时
        #  没有问题，但是如果数据存储在文件中，需要优化存储和读取过程
        #  ，以便提高效率。目前优化了csv文件的读取，通过分块读取提高
        #  csv文件的读取效率，其他文件系统的读取还需要进一步优化
        if not isinstance(table, str):
            err = TypeError(f'table name should be a string, got {type(table)} instead.')
            raise err
        if table not in TABLE_MASTERS.keys():
            raise KeyError(f'Invalid table name: {table}.')

        if shares is not None:
            assert isinstance(shares, (str, list))
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
                warnings.warn(f'can not find share-like primary key in the table {table}!\n'
                              f'passed argument shares will be ignored!', RuntimeWarning)
        # 识别Primary key中的，并确认是否需要筛选日期型pk
        if (start is not None) and (end is not None):
            try:
                date_like_dtype = [item for item in pk_dtypes if item in ['date', 'datetime']][0]
                date_like_pk = primary_key[pk_dtypes.index(date_like_dtype)]
            except Exception as e:
                warnings.warn(f'{e}\ncan not find date-like primary key in the table {table}!\n'
                              f'passed start({start}) and end({end}) arguments will be ignored!', RuntimeWarning)

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
            if share_like_pk is not None:
                df = df.loc[df.index.isin(shares, level=share_like_pk)]
            if date_like_pk is not None:
                # 两种方法实现筛选，分别是df.query 以及 df.index.get_level_values()
                # 第一种方法， df.query
                # df = df.query(f"{date_like_pk} >= {start} and {date_like_pk} <= {end}")
                # 第二种方法：df.index.get_level_values()
                m1 = df.index.get_level_values(date_like_pk) >= start
                m2 = df.index.get_level_values(date_like_pk) <= end
                df = df[m1 & m2]
        elif self.source_type == 'db':
            # 读取数据库表，从数据库表中读取的DataFrame并未设置primary_key index，因此
            # 需要手动设置index，但是读取的数据已经按shares/start/end筛选，无需手动筛选
            if not self._db_table_exists(db_table=table):
                # 如果数据库中不存在该表，则创建表
                self._new_db_table(db_table=table, columns=columns, dtypes=dtypes, primary_key=primary_key)
            if share_like_pk is None:
                shares = None
            if date_like_pk is None:
                start = None
                end = None
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
            raise FileExistsError(f'File {file_path_name} already exists!')

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
        if self.source_type == 'file':
            df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtype)
            set_primary_key_index(df, primary_key=primary_key, pk_dtypes=pk_dtype)
            rows_affected = self._write_file(df, file_name=table)
        elif self.source_type == 'db':
            df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtype)
            if not self._db_table_exists(table):
                self._new_db_table(db_table=table, columns=columns, dtypes=dtypes, primary_key=primary_key)
            if on_duplicate == 'ignore':
                rows_affected = self._write_database(df, db_table=table, primary_key=primary_key)
            elif on_duplicate == 'update':
                rows_affected = self._update_database(df, db_table=table, primary_key=primary_key)
            else:  # for unexpected cases
                raise KeyError(f'Invalid process mode on duplication: {on_duplicate}')
        self._table_list.add(table)
        return rows_affected

    def fetch_history_table_data(self, table, channel='tushare', df=None, f_name=None, **kwargs):
        """从网络获取本地数据表的历史数据，并进行内容写入前的预处理：

        数据预处理包含以下步骤：
        1，根据channel确定数据源，根据table名下载相应的数据表
        2，处理获取的df的格式，确保为只含简单range-index的格式

        Parameters
        ----------
        table: str,
            数据表名，必须是database中定义的数据表
        channel: str, optional
            str: 数据获取渠道，指定本地文件、金融数据API，或直接给出local_df，支持以下选项：
            - 'df'      : 通过参数传递一个df，该df的columns必须与table的定义相同
            - 'csv'     : 通过本地csv文件导入数据，此时必须给出f_name参数
            - 'excel'   : 通过一个Excel文件导入数据，此时必须给出f_name参数
            - 'tushare' : 从Tushare API获取金融数据，请自行申请相应权限和积分
            - 'other'   : NotImplemented 其他金融数据API，尚未开发
        df: pd.DataFrame
            通过传递一个DataFrame获取数据, 如果数据获取渠道为"df"，则必须给出此参数
        f_name: str 通过本地csv文件或excel文件获取数据
            如果数据获取方式为"csv"或者"excel"时，必须给出此参数，表示文件的路径
        **kwargs:
            用于下载金融数据的函数参数，或者读取本地csv文件的函数参数

        Returns
        -------
        pd.DataFrame:
            下载后并处理完毕的数据，DataFrame形式，仅含简单range-index格式
        """
        # TODO: 将该函数移动到别的文件中如datachannels.py
        #  这个函数的功能与DataSource的定义不符。
        #  在DataSource中应该有一个API专司数据的清洗，以便任何形式的数据都
        #  可以在清洗后被写入特定的数据表，而数据的获取则不应该放在DataSource中
        #  DataSource应该被设计为专精与数据的存储接口，而不是数据获取接口
        #  同样的道理适用于refill_local_source()函数

        # 目前仅支持从tushare获取数据，未来可能增加新的API
        from .tsfuncs import acquire_data
        if not isinstance(table, str):
            err = TypeError(f'table name should be a string, got {type(table)} instead.')
            raise err
        if table not in TABLE_MASTERS.keys():
            raise KeyError(f'Invalid table name {table}')
        if not isinstance(channel, str):
            err = TypeError(f'channel should be a string, got {type(channel)} instead.')
            raise err
        if channel not in AVAILABLE_CHANNELS:
            raise KeyError(f'Invalid channel name {channel}')

        column, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
        # 从指定的channel获取数据
        if channel == 'df':
            # 通过参数传递的DF获取数据
            if df is None:
                err = ValueError(f'a DataFrame must be given while channel == "df"')
                raise err
            if not isinstance(df, pd.DataFrame):
                err = TypeError(f'local df should be a DataFrame, got {type(df)} instead.')
                raise err
            dnld_data = df
        elif channel == 'csv':
            # 读取本地csv数据文件获取数据
            if f_name is None:
                err = ValueError(f'a file path and name must be given while channel == "csv"')
                raise err
            if not isinstance(f_name, str):
                err = TypeError(f'file name should be a string, got {type(df)} instead.')
                raise err
            dnld_data = pd.read_csv(f_name, **kwargs)
        elif channel == 'excel':
            # 读取本地Excel文件获取数据
            assert f_name is not None, f'a file path and name must be given while channel == "excel"'
            assert isinstance(f_name, str), \
                f'file name should be a string, got {type(df)} instead.'
            raise NotImplementedError
        elif channel == 'tushare':
            # 通过tushare的API下载数据
            api_name = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('tushare')]
            try:
                dnld_data = acquire_data(api_name, **kwargs)
            except Exception as e:
                raise Exception(f'{e}: data {table} can not be acquired from tushare')
        else:
            raise NotImplementedError
        res = set_primary_key_frame(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
        return res

    def fetch_realtime_price_data(self, table, channel, symbols):
        """ 获取分钟级实时股票价格数据，并进行内容写入前的预处理, 目前只支持下面的数据表获取实时分钟数据：
        stock_1min/stock_5min/stock_15min/stock_30min/stock_hourly

        Parameters
        ----------
        table: str,
            数据表名，必须是database中定义的数据表
        channel: str,
            数据获取渠道，金融数据API，支持以下选项:
            - 'eastmoney': 通过东方财富网的API获取数据
            - 'tushare':   从Tushare API获取金融数据，请自行申请相应权限和积分
            - 'other':     NotImplemented 其他金融数据API，尚未开发
        symbols: str or list of str
            用于下载金融数据的函数参数，需要输入完整的ts_code，表示股票代码

        Returns
        -------
        pd.DataFrame:
            下载后并处理完毕的数据，DataFrame形式，仅含简单range-index格式
            columns: ts_code, trade_time, open, high, low, close, vol, amount
        """

        # TODO: 将该函数移动到别的文件中如datachannels.py
        #  这个函数的功能与DataSource的定义不符。
        #  在DataSource中应该有一个API专司数据的清洗，以便任何形式的数据都
        #  可以在清洗后被写入特定的数据表，而数据的获取则不应该放在DataSource中
        #  DataSource应该被设计为专精与数据的存储接口，而不是数据获取接口
        #  同样的道理适用于refill_local_source()函数

        # 目前支持从tushare和eastmoney获取数据，未来可能增加新的API
        if not isinstance(table, str):
            err = TypeError(f'table name should be a string, got {type(table)} instead.')
            raise err
        if table not in ['stock_1min', 'stock_5min', 'stock_15min', 'stock_30min', 'stock_hourly']:
            raise KeyError(f'realtime minute data is not available for table {table}')

        table_freq_map = {
            '1min':  '1MIN',
            '5min':  '5MIN',
            '15min': '15MIN',
            '30min': '30MIN',
            'h':     '60MIN',
        }

        table_freq = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('freq')]
        realtime_data_freq = table_freq_map[table_freq]
        # 从指定的channel获取数据
        if channel == 'tushare':
            # tushare 要求symbols以逗号分隔字符串形式给出
            if isinstance(symbols, list):
                symbols = ','.join(symbols)
            from .tsfuncs import acquire_data as acquire_data_from_ts
            # 通过tushare的API下载数据
            api_name = 'realtime_min'
            if symbols is None:
                err = ValueError(f'ts_code must be given while channel == "tushare"')
                raise err
            try:
                dnld_data = acquire_data_from_ts(api_name, ts_code=symbols, freq=realtime_data_freq)
            except Exception as e:
                raise Exception(f'data {table} can not be acquired from tushare\n{e}')

            # 从下载的数据中提取出需要的列
            dnld_data = dnld_data[['code', 'time', 'open', 'high', 'low', 'close', 'volume', 'amount']]
            dnld_data = dnld_data.rename(columns={
                'code':   'ts_code',
                'time':   'trade_time',
                'volume': 'vol',
            })

            return dnld_data
        # 通过东方财富网的API下载数据
        elif channel == 'eastmoney':
            from .emfuncs import acquire_data as acquire_data_from_em
            if isinstance(symbols, str):
                # 此时symbols应该以字符串列表的形式给出
                symbols = str_to_list(symbols)
            result_data = pd.DataFrame(
                    columns=['ts_code', 'trade_time', 'open', 'high', 'low', 'close', 'vol', 'amount'],
            )
            table_freq_map = {
                '1min':  1,
                '5min':  5,
                '15min': 15,
                '30min': 30,
                'h':     60,
            }
            current_time = pd.to_datetime('today')
            # begin time is freq minutes before current time
            begin_time = current_time.strftime('%Y%m%d')
            for symbol in symbols:
                code = symbol.split('.')[0]
                dnld_data = acquire_data_from_em(
                        api_name='get_k_history',
                        code=code,
                        beg=begin_time,
                        klt=table_freq_map[table_freq],
                        fqt=0,  # 获取不复权数据
                )
                # 仅保留dnld_data的最后一行，并添加ts_code列，值为symbol
                dnld_data = dnld_data.iloc[-1:, :]
                dnld_data['ts_code'] = symbol
                # 将dnld_data合并到result_data的最后一行 # TODO: 检查是否需要ignore_index参数？此时index信息会丢失

                result_data = pd.concat([result_data, dnld_data], axis=0, ignore_index=True)

            return result_data
        else:
            raise NotImplementedError

    def update_table_data(self, table, df, merge_type='update'):
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
            # 如果source_type == 'db'，不需要合并数据，当merge_type == 'update'时，甚至不需要下载
            # 本地数据
            if merge_type == 'ignore':
                dnld_data_range = get_primary_key_range(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
                local_data = self.read_table_data(table, **dnld_data_range)
                set_primary_key_index(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
                dnld_data = dnld_data[~dnld_data.index.isin(local_data.index)]
            dnld_data = set_primary_key_frame(dnld_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
            rows_affected = self.write_table_data(df=dnld_data, table=table, on_duplicate=merge_type)
        else:  # unexpected case
            raise KeyError(f'invalid data source type: {self.source_type}')

        return rows_affected

    def drop_table_data(self, table):
        """ 删除本地存储的数据表(操作不可撤销，谨慎使用)

        Parameters
        ----------
        table: str,
            本地数据表的名称

        Returns
        -------
        None
        """
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
        return {'table': table,
                'table_exists': table_exists,
                'table_size': table_size,
                'table_rows': table_rows,
                'primary_key1': pk1,
                'pk_records1': pk_records1,
                'pk_min1': pk_min1,
                'pk_max1': pk_max1,
                'primary_key2': pk2,
                'pk_records2': pk_records2,
                'pk_min2': pk_min2,
                'pk_max2': pk_max2
                }

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

            import pymysql
            con = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.__user__,
                    password=self.__password__,
                    db=self.db_name,
            )
            cursor = con.cursor()
            columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table, with_primary_keys=True)
            primary_key = primary_keys[0]
            sql = f"SELECT * FROM `{table}` ORDER BY `{primary_key}` DESC LIMIT 1;"
            try:
                cursor.execute(sql)
                con.commit()
                res = cursor.fetchall()
                return res[0][0] if len(res) > 0 else 0
            except Exception as e:
                err = RuntimeError(
                    f'{e}, An error occurred when getting last record_id for table {table} with SQL:\n{sql}')
                raise err
            finally:
                con.close()

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

        return res_df

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

    def update_sys_table_data(self, table:str, record_id:int, **data) -> int:
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

    def insert_sys_table_data(self, table:str, **data) -> int:
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
        self.update_table_data(table, df, merge_type='update')
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
    # 特殊函数，包括用于组合HistoryPanel的数据获取接口函数，以及自动或手动下载本地数据的操作函数
    # ==============
    def get_history_data(self, shares=None, symbols=None, htypes=None, freq='d', start=None, end=None, row_count=100,
                         asset_type='any', adj='none'):
        """ 根据给出的参数从不同的本地数据表中获取数据，并打包成一系列的DataFrame，以便组装成
            HistoryPanel对象。

        Parameters
        ----------
        shares: str or list of str
            等同于新的symbols参数，为了兼容旧的代码，保留此参数
            需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
            如以下两种输入方式皆合法且等效：
             - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
             - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
        symbols: str or list of str
            需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
            如以下两种输入方式皆合法且等效：
             - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
             - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']
        htypes: str or list of str
            需要获取的历史数据类型集合，可以是以逗号分隔的数据类型字符串或者数据类型字符列表，
            如以下两种输入方式皆合法且等效：
             - str:     'open, high, low, close'
             - list:    ['open', 'high', 'low', 'close']
        freq: str
            获取的历史数据的频率，包括以下选项：
             - 1/5/15/30min 1/5/15/30分钟频率周期数据(如K线)
             - H/D/W/M 分别代表小时/天/周/月 周期数据(如K线)
             如果下载的数据频率与目标freq不相同，将通过升频或降频使其与目标频率相同
        start: str, optional
            YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
        end: str, optional
            YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
        row_count: int, optional, default 10
            获取的历史数据的行数，如果指定了start和end，则忽略此参数
        asset_type: str or list of str
            限定获取的数据中包含的资产种类，包含以下选项或下面选项的组合，合法的组合方式包括
            逗号分隔字符串或字符串列表，例如: 'E, IDX' 和 ['E', 'IDX']都是合法输入
             - any: 可以获取任意资产类型的证券数据(默认值)
             - E:   只获取股票类型证券的数据
             - IDX: 只获取指数类型证券的数据
             - FT:  只获取期货类型证券的数据
             - FD:  只获取基金类型证券的数据
        adj: str
            对于某些数据，可以获取复权数据，需要通过复权因子计算，复权选项包括：
             - none / n: 不复权(默认值)
             - back / b: 后复权
             - forward / fw / f: 前复权

        Returns
        -------
        Dict of DataFrame: {htype: DataFrame[shares]}
            一个标准的DataFrame-Dict，满足stack_dataframes()函数的输入要求，以便组装成
            HistoryPanel对象
        """
        if symbols is not None:
            shares = symbols
        if isinstance(htypes, str):
            htypes = str_to_list(htypes)
        if isinstance(shares, str):
            shares = str_to_list(shares)
        if isinstance(asset_type, str):
            if asset_type.lower() == 'any':
                from qteasy.utilfuncs import AVAILABLE_ASSET_TYPES
                asset_type = AVAILABLE_ASSET_TYPES
            else:
                asset_type = str_to_list(asset_type)

        # 根据资产类型、数据类型和频率找到应该下载数据的目标数据表，以及目标列
        table_master = get_table_master()
        # 设置soft_freq = True以通过抖动频率查找频率不同但类型相同的数据表
        tables_to_read = htype_to_table_col(
                htypes=htypes,
                freq=freq,
                asset_type=asset_type,
                soft_freq=True
        )
        table_data_acquired = {}
        table_data_columns = {}
        if (start is not None) or (end is not None):
            # 如果指定了start或end，则忽略row_count参数, 但是如果row_count为None，则默认为-1, 读取所有数据
            row_count = 0 if row_count is not None else -1
        # 逐个读取相关数据表，删除名称与数据类型不同的，保存到一个字典中，这个字典的键为表名，值为读取的DataFrame
        for tbl, columns in tables_to_read.items():
            df = self.read_table_data(tbl, shares=shares, start=start, end=end)
            if not df.empty:
                cols_to_drop = [col for col in df.columns if col not in columns]
                df.drop(columns=cols_to_drop, inplace=True)
                if row_count > 0:
                    # 读取每一个ts_code的最后row_count行数据
                    df = df.groupby('ts_code').tail(row_count)
            table_data_acquired[tbl] = df
            table_data_columns[tbl] = df.columns
        # 从读取的数据表中提取数据，生成单个数据类型的dataframe，并把各个dataframe合并起来
        # 在df_by_htypes中预先存储了多个空DataFrame，用于逐个合并相关的历史数据
        df_by_htypes = {k: v for k, v in zip(htypes, [pd.DataFrame()] * len(htypes))}
        for htyp in htypes:
            for tbl in tables_to_read:
                if htyp in table_data_columns[tbl]:
                    df = table_data_acquired[tbl]
                    # 从本地读取的DF中的数据是按multi_index的形式stack起来的，因此需要unstack，成为多列、单index的数据
                    if not df.empty:
                        htyp_series = df[htyp]
                        new_df = htyp_series.unstack(level=0)
                        old_df = df_by_htypes[htyp]
                        # 使用两种方法实现df的合并，分别是merge()和join()
                        # df_by_htypes[htyp] = old_df.merge(new_df,
                        #                                   how='outer',
                        #                                   left_index=True,
                        #                                   right_index=True,
                        #                                   suffixes=('', '_y'))
                        df_by_htypes[htyp] = old_df.join(new_df,
                                                         how='outer',
                                                         rsuffix='_y')

        # 如果在历史数据合并后发现列名称冲突，发出警告信息，并删除后添加的列
        conflict_cols = ''
        for htyp in htypes:
            df_columns = df_by_htypes[htyp].columns.to_list()
            col_with_suffix = [col for col in df_columns if col[-2:] == '_y']
            if len(col_with_suffix) > 0:
                df_by_htypes[htyp].drop(columns=col_with_suffix, inplace=True)
                conflict_cols += f'd-type {htyp} conflicts in {list(set(col[:-2] for col in col_with_suffix))};\n'
        if conflict_cols != '':
            warnings.warn(f'\nConflict data encountered, some types of data are loaded from multiple tables, '
                          f'conflicting data might be discarded:\n'
                          f'{conflict_cols}', DataConflictWarning)
        # 如果提取的数据全部为空DF，说明DataSource可能数据不足，报错并建议
        if all(df.empty for df in df_by_htypes.values()):
            err = RuntimeError(f'Empty data extracted from DataSource {self.connection_type} with parameters:\n'
                               f'shares: {shares}\n'
                               f'htypes: {htypes}\n'
                               f'start/end/freq: {start}/{end}/"{freq}"\n'
                               f'asset_type/adj: {asset_type} / {adj}\n'
                               f'To check data availability, use one of the following:\n'
                               f'Availability of all tables:     qt.get_table_overview()，or\n'
                               f'Availability of <table_name>:   qt.get_table_info(\'table_name\')\n'
                               f'To fill datasource:             qt.refill_data_source(table=\'table_name\', '
                               f'**kwargs)')
            raise err
        # 如果需要复权数据，计算复权价格
        adj_factors = {}
        if adj.lower() not in ['none', 'n']:
            # 下载复权因子
            adj_tables_to_read = table_master.loc[(table_master.table_usage == 'adj') &
                                                  table_master.asset_type.isin(asset_type)].index.to_list()
            for tbl in adj_tables_to_read:
                adj_df = self.read_table_data(tbl, shares=shares, start=start, end=end)
                if not adj_df.empty:
                    adj_df = adj_df['adj_factor'].unstack(level=0)
                adj_factors[tbl] = adj_df
            # 如果adj table不为空但无法读取adj因子，则报错
            if adj_tables_to_read and (not adj_factors):
                err = ValueError(f'Failed reading price adjust factor data. call "qt.get_table_info()" to '
                                 f'check local source data availability')
                raise err

        if adj_factors:
            # 根据复权因子更新所有可复权数据
            prices_to_adjust = [item for item in htypes if item in ADJUSTABLE_PRICE_TYPES]
            for htyp in prices_to_adjust:
                price_df = df_by_htypes[htyp]
                all_ts_codes = price_df.columns
                combined_factors = 1.0
                # 后复权价 = 当日最新价 × 当日复权因子
                for af in adj_factors:
                    combined_factors *= adj_factors[af].reindex(columns=all_ts_codes, index=price_df.index).fillna(1.0)
                # 得到合并后的复权因子，如果数据的频率为日级(包括周、月)，直接相乘即可
                #  但如果数据的频率是分钟级，则需要将复权因子也扩展到分钟级，才能相乘
                if freq in ['min', '1min', '5min', '15min', '30min', 'h']:
                    expanded_factors = combined_factors.reindex(price_df.index.date)
                    expanded_factors.index = price_df.index
                    price_df *= expanded_factors
                else:
                    price_df *= combined_factors
                # 前复权价 = 当日复权价 ÷ 最新复权因子
                if adj.lower() in ['forward', 'fw', 'f'] and len(combined_factors) > 1:
                    price_df /= combined_factors.iloc[-1]

        # 最后整理数据，确保每一个htype的数据框的columns与shares相同
        for htyp, df in df_by_htypes.items():
            df_by_htypes[htyp] = df.reindex(columns=shares)
        # print(f'[DEBUG]: in database.py get_history_data() got db_by_htypes:\n{df_by_htypes}')
        return df_by_htypes

    def get_index_weights(self, index, start=None, end=None, shares=None):
        """ 从本地数据仓库中获取一个指数的成分权重

        Parameters
        ----------
        index: [str, list]
            需要获取成分的指数代码，可以包含多个指数，每个指数
        start: str
            YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的开始日期/时间(如果可用)
        end: str
            YYYYMMDD HH:MM:SS 格式的日期/时间，获取的历史数据的结束日期/时间(如果可用)
        shares: [str, list]
            需要获取历史数据的证券代码集合，可以是以逗号分隔的证券代码字符串或者证券代码字符列表，
            如以下两种输入方式皆合法且等效：
             - str:     '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ'
             - list:    ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']

        Returns
        -------
        Dict 一个标准的DataFrame-Dict，满足stack_dataframes()函数的输入要求，以便组装成
            HistoryPanel对象
        """
        if isinstance(index, str):
            index = str_to_list(index)
        if isinstance(shares, str):
            shares = str_to_list(shares)
        # 读取时间内的权重数据
        weight_data = self.read_table_data('index_weight', shares=index, start=start, end=end)
        if not weight_data.empty:
            weight_data = weight_data.unstack()
        else:
            # return empty dict
            return {}
        weight_data.columns = weight_data.columns.get_level_values(1)
        all_shares = weight_data.columns
        df_by_index = {}
        index_names = []
        columns_to_drop = []
        indices_found = weight_data.index.get_level_values(0)
        # 整理读取数据的结构，删除不需要的股票， 添加额外的股票，整理顺序
        if shares is not None:
            if isinstance(shares, str):
                shares = str_to_list(shares)
            columns_to_drop = [item for item in all_shares if item not in shares]
        for idx in index:
            if idx in indices_found:
                weight_df = weight_data.loc[idx]
            else:
                weight_df = pd.DataFrame(columns=all_shares)
            index_names.append(idx)
            if shares is not None:
                weight_df.drop(columns=columns_to_drop, inplace=True)
                weight_df = weight_df.reindex(columns=shares)
            df_by_index['wt-' + idx] = weight_df
        return df_by_index

    def refill_local_source(self, tables=None, dtypes=None, freqs=None, asset_types=None, start_date=None,
                            end_date=None, list_arg_filter=None, symbols=None, merge_type='update',
                            reversed_par_seq=False, parallel=True, process_count=None, chunk_size=100,
                            download_batch_size=0, download_batch_interval=0, refresh_trade_calendar=False,
                            log=False) -> None:
        """ 批量下载历史数据并保存到本地数据仓库

        Parameters
        ----------
        tables: str or list of str
            需要补充的本地数据表，可以同时给出多个table的名称，逗号分隔字符串和字符串列表都合法：
            例如，下面两种方式都合法且相同：
                table='stock_indicator, stock_daily, income, stock_adj_factor'
                table=['stock_indicator', 'stock_daily', 'income', 'stock_adj_factor']
            除了直接给出表名称以外，还可以通过表类型指明多个表，可以同时输入多个类型的表：
                - 'all'     : 所有的表
                - 'cal'     : 交易日历表
                - 'basics'  : 所有的基础信息表
                - 'adj'     : 所有的复权因子表
                - 'data'    : 所有的历史数据表
                - 'events'  : 所有的历史事件表(如股票更名、更换基金经理、基金份额变动等)
                - 'report'  : 财务报表
                - 'comp'    : 指数成分表
        dtypes: str or list of str
            通过指定dtypes来确定需要更新的表单，只要包含指定的dtype的数据表都会被选中
            如果给出了tables，则dtypes参数会被忽略
        freqs: str or list of str
            通过指定tables或dtypes来确定需要更新的表单时，指定freqs可以限定表单的范围
            如果tables != all时，给出freq会排除掉freq与之不符的数据表
        asset_types: str or list of str
            通过指定tables或dtypes来确定需要更新的表单时，指定asset_types可以限定表单的范围
            如果tables != all时，给出asset_type会排除掉与之不符的数据表
        start_date: str YYYYMMDD
            限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
        end_date: str YYYYMMDD
            限定数据下载的时间范围，如果给出start_date/end_date，只有这个时间段内的数据会被下载
        list_arg_filter: str or list of str, default: None  **注意，不是所有情况下filter_arg参数都有效**
            限定下载数据时的筛选参数，某些数据表以列表的形式给出可筛选参数，如stock_basic表，它有一个可筛选
            参数"exchange"，选项包含 'SSE', 'SZSE', 'BSE'，可以通过此参数限定下载数据的范围。
            如果filter_arg为None，则下载所有数据。
            例如，下载stock_basic表数据时，下载以下输入均为合法输入：
            - 'SZSE'
                仅下载深圳交易所的股票数据
            - ['SSE', 'SZSE']
            - 'SSE, SZSE'
                上面两种写法等效，下载上海和深圳交易所的股票数据
        symbols: str or list of str
            限定下载数据的证券代码范围，代码不需要给出类型后缀，只需要给出数字代码即可。
            可以多种形式确定范围，以下输入均为合法输入：
            - '000001'
                没有指定asset_types时，000001.SZ, 000001.SH ... 等所有代码都会被选中下载
                如果指定asset_types，只有符合类型的证券数据会被下载
            - '000001, 000002, 000003'
            - ['000001', '000002', '000003']
                两种写法等效，列表中列举出的证券数据会被下载
            - '000001:000300'
                从'000001'开始到'000300'之间的所有证券数据都会被下载
        merge_type: str, Default update
            数据混合方式，当获取的数据与本地数据的key重复时，如何处理重复的数据：
            - 'update' 默认值，下载并更新本地数据的重复部分，使用下载的数据覆盖本地数据
            - 'ignore' 不覆盖本地的数据，在将数据复制到本地时，先去掉本地已经存在的数据，会导致速度降低
        reversed_par_seq: Bool, Default False
            是否逆序参数下载数据， 默认False
            - True:  逆序参数下载数据
            - False: 顺序参数下载数据
        parallel: Bool, Default True
            是否启用多线程下载数据
            - True:  启用多线程下载数据
            - False: 禁用多线程下载
        process_count: int
            启用多线程下载时，同时开启的线程数，默认值为设备的CPU核心数
        chunk_size: int
            保存数据到本地时，为了减少文件/数据库读取次数，将下载的数据累计一定数量后
            再批量保存到本地，chunk_size即批量，默认值100
        download_batch_size: int, default 0
            为了降低下载数据时的网络请求频率，可以在完成一批数据下载后，暂停一段时间再继续下载
            该参数指定了每次暂停之前最多可以下载的次数，该参数只有在parallel=False时有效
            如果为0，则不暂停，一次性下载所有数据
        download_batch_interval: int, default 0
            为了降低下载数据时的网络请求频率，可以在完成一批数据下载后，暂停一段时间再继续下载
            该参数指定了每次暂停的时间，单位为秒，该参数只有在parallel=False时有效
            如果<=0，则不暂停，立即开始下一批数据下载
        refresh_trade_calendar: Bool, Default False
            是否强制刷新交易日历，如果为True，将下载最新的交易日历数据，如果为False，仅在交易日历数据不足时下载
        log: Bool, Default False
            是否记录数据下载日志

        Returns
        -------
        None

        """

        from .tsfuncs import acquire_data
        # 1 参数合法性检查 TODO: 参数检查在core.py中完成，这里只需要调用即可
        if (tables is None) and (dtypes is None):
            raise KeyError(f'tables and dtypes can not both be None.')
        if tables is None:
            tables = []
        if dtypes is None:
            dtypes = []
        valid_table_values = list(TABLE_MASTERS.keys()) + TABLE_USAGES + ['all']
        if not isinstance(tables, (str, list)):
            err = TypeError(f'tables should be a list or a string, got {type(tables)} instead.')
            raise err
        if isinstance(tables, str):
            tables = str_to_list(tables)
        if not all(item.lower() in valid_table_values for item in tables):
            raise KeyError(f'some items in tables list are not valid: '
                           f'{[item for item in tables if item not in valid_table_values]}')
        if not isinstance(dtypes, (str, list)):
            err = TypeError(f'dtypes should be a list of a string, got {type(dtypes)} instead.')
            raise err
        if isinstance(dtypes, str):
            dtypes = str_to_list(dtypes)

        if chunk_size <= 0:
            chunk_size = 100

        if download_batch_size <= 0:
            download_batch_size = 999999999999  # 一个很大的数，保证不会暂停下载

        if download_batch_interval <= 0:
            download_batch_interval = 0

        code_start = None
        code_end = None
        if symbols is not None:
            if not isinstance(symbols, (str, list)):
                err = TypeError(f'code_range should be a string or list, got {type(symbols)} instead.')
                raise err
            if isinstance(symbols, str):
                if len(str_to_list(symbols, ':')) == 2:
                    code_start, code_end = str_to_list(symbols, ':')
                    symbols = None
                else:
                    symbols = str_to_list(symbols, ',')

        if list_arg_filter is not None:
            if not isinstance(list_arg_filter, (str, list)):
                err = TypeError(f'list_arg_filter should be a string or list, got {type(list_arg_filter)} instead.')
                raise err
            if isinstance(list_arg_filter, str):
                list_arg_filter = str_to_list(list_arg_filter, ',')

        # 2 生成需要处理的数据表清单 tables
        table_master = get_table_master()
        tables_to_refill = set()
        tables = [item.lower() for item in tables]
        if 'all' in tables:
            tables_to_refill.update(TABLE_MASTERS)
        else:
            for item in tables:
                if item in TABLE_MASTERS:
                    tables_to_refill.add(item)
                elif item in TABLE_USAGES:
                    tables_to_refill.update(
                            table_master.loc[table_master.table_usage == item.lower()].index.to_list()
                    )
            for item in dtypes:  # 如果给出了dtypes，进一步筛选tables中的表，删除不需要的
                tables_to_keep = set()
                for tbl, schema in table_master.schema.items():  # iteritems()在pandas中已经被废弃
                    if item.lower() in TABLE_SCHEMA[schema]['columns']:
                        tables_to_keep.add(tbl)
                tables_to_refill.intersection_update(
                        tables_to_keep
                )

            if freqs is not None:
                tables_to_keep = set()
                for freq in str_to_list(freqs):
                    tables_to_keep.update(
                            table_master.loc[table_master.freq == freq.lower()].index.to_list()
                    )
                tables_to_refill.intersection_update(
                        tables_to_keep
                )
            if asset_types is not None:
                tables_to_keep = set()
                for a_type in str_to_list(asset_types):
                    tables_to_keep.update(
                            table_master.loc[table_master.asset_type == a_type.upper()].index.to_list()
                    )
                tables_to_refill.intersection_update(
                        tables_to_keep
                )

            dependent_tables = set()
            for table in tables_to_refill:
                cur_table = table_master.loc[table]
                fill_type = cur_table.fill_arg_type
                if fill_type == 'trade_date' and refresh_trade_calendar:
                    dependent_tables.add('trade_calendar')
                elif fill_type == 'table_index':
                    dependent_tables.add(cur_table.arg_rng)
            tables_to_refill.update(dependent_tables)

            # 检查trade_calendar中是否有足够的数据，如果没有，需要包含trade_calendar表：
            if 'trade_calendar' not in tables_to_refill:
                if refresh_trade_calendar:
                    tables_to_refill.add('trade_calendar')
                else:
                    # 检查trade_calendar中是否已有数据，且最新日期是否足以覆盖今天，如果没有数据或数据不足，也需要添加该表
                    latest_calendar_date = self.get_table_info('trade_calendar', print_info=False)['pk_max2']
                    try:
                        latest_calendar_date = pd.to_datetime(latest_calendar_date)
                        if pd.to_datetime('today') >= pd.to_datetime(latest_calendar_date):
                            tables_to_refill.add('trade_calendar')
                    except:
                        tables_to_refill.add('trade_calendar')

        # 开始逐个下载清单中的表数据
        table_count = 0
        import time
        for table in table_master.index:
            # 逐个下载数据并写入本地数据表中
            if table not in tables_to_refill:
                continue
            table_count += 1
            cur_table_info = table_master.loc[table]
            # 3 生成数据下载参数序列
            arg_name = cur_table_info.fill_arg_name
            fill_type = cur_table_info.fill_arg_type
            freq = cur_table_info.freq

            # 开始生成所有的参数，参数的生成取决于fill_arg_type
            if (start_date is None) and (fill_type in ['datetime', 'trade_date']):
                start = cur_table_info.arg_rng
            else:
                start = start_date
            if start is not None:
                start = pd.to_datetime(start).strftime('%Y%m%d')
            if end_date is None:
                end = 'today'
            else:
                end = end_date
            end = pd.to_datetime(end).strftime('%Y%m%d')
            allow_start_end = (cur_table_info.arg_allow_start_end.lower() == 'y')
            start_end_chunk_size = 0
            if cur_table_info.start_end_chunk_size != '':
                start_end_chunk_size = int(cur_table_info.start_end_chunk_size)
            additional_args = {}
            chunked_additional_args = []
            start_end_chunk_multiplier = 1
            # 生成start和end参数，如果需要的话
            if allow_start_end:
                additional_args = {'start': start, 'end': end}
            if start_end_chunk_size > 0:
                start_end_chunk_lbounds = list(pd.date_range(start=start,
                                                             end=end,
                                                             freq=f'{start_end_chunk_size}d'
                                                             ).strftime('%Y%m%d'))
                start_end_chunk_rbounds = start_end_chunk_lbounds[1:]
                # 取到的日线或更低频率数据是包括右边界的，去掉右边界可以得到更精确的结果
                # 但是这样做可能没有意义
                if freq.upper() in ['D', 'W', 'M']:
                    prev_day = pd.Timedelta(1, 'd')
                    start_end_chunk_rbounds = pd.to_datetime(start_end_chunk_lbounds[1:]) - prev_day
                    start_end_chunk_rbounds = list(start_end_chunk_rbounds.strftime('%Y%m%d'))

                start_end_chunk_rbounds.append(end)
                chunked_additional_args = [{'start': s, 'end': e} for s, e in
                                           zip(start_end_chunk_lbounds, start_end_chunk_rbounds)]
                start_end_chunk_multiplier = len(chunked_additional_args)
            # 生成其他参数，根据不同的fill_type生成不同的参数序列
            if fill_type in ['datetime', 'trade_date']:
                # 根据start_date和end_date生成数据获取区间
                additional_args = {}  # 使用日期作为关键参数，不再需要additional_args
                arg_coverage = pd.date_range(start=start, end=end, freq=freq)
                if fill_type == 'trade_date':
                    if freq.lower() in ['m', 'w', 'w-Fri']:
                        # 当生成的日期不连续时，或要求生成交易日序列时，需要找到最近的交易日
                        arg_coverage = map(nearest_market_trade_day, arg_coverage)
                    if freq == 'd':
                        arg_coverage = (date for date in arg_coverage if is_market_trade_day(date))
                arg_coverage = list(pd.to_datetime(list(arg_coverage)).strftime('%Y%m%d'))
            elif fill_type == 'list':
                # 如果参数是一个列表，直接使用这个列表作为参数序列，除非给出了list_arg_filter
                arg_coverage = str_to_list(cur_table_info.arg_rng) if list_arg_filter is None else list_arg_filter
            elif fill_type == 'table_index':
                suffix = str_to_list(cur_table_info.arg_allowed_code_suffix)
                source_table = self.read_table_data(cur_table_info.arg_rng)
                arg_coverage = source_table.index.to_list()
                if code_start is not None:
                    arg_coverage = [code for code in arg_coverage if (code_start <= code.split('.')[0] <= code_end)]
                if symbols is not None:
                    arg_coverage = [code for code in arg_coverage if code.split('.')[0] in symbols]
                if suffix:
                    arg_coverage = [code for code in arg_coverage if code.split('.')[1] in suffix]
            else:
                arg_coverage = []

            # 处理数据下载参数序列，剔除已经存在的数据key
            if self.table_data_exists(table) and merge_type.lower() == 'ignore':
                # 当数据已经存在，且合并模式为"忽略新数据"时，从计划下载的数据范围中剔除已经存在的部分
                already_existed = self.get_table_data_coverage(table, arg_name)
                arg_coverage = [arg for arg in arg_coverage if arg not in already_existed]

            # 生成所有的参数, 开始循环下载并更新数据
            if reversed_par_seq:
                arg_coverage.reverse()
            if chunked_additional_args:
                import itertools
                all_kwargs = ({arg_name: val, **add_arg} for val, add_arg in
                              itertools.product(arg_coverage, chunked_additional_args))
            else:
                all_kwargs = ({arg_name: val, **additional_args} for val in arg_coverage)

            completed = 0
            total = len(list(arg_coverage)) * start_end_chunk_multiplier
            total_written = 0
            st = time.time()
            dnld_data = pd.DataFrame()
            time_elapsed = 0
            rows_affected = 0
            try:
                # 清单中的第一张表不使用parallel下载
                if parallel and table_count != 1:
                    with ThreadPoolExecutor(max_workers=process_count) as worker:
                        '''
                        这里如果直接使用fetch_history_table_data会导致程序无法运行，原因不明，目前只能默认通过tushare接口获取数据
                        通过TABLE_MASTERS获取tushare接口名称，并通过acquire_data直接通过tushare的API获取数据
                        '''
                        api_name = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('tushare')]
                        futures = {}
                        submitted = 0
                        for kw in all_kwargs:
                            futures.update({worker.submit(acquire_data, api_name, **kw): kw})
                            submitted += 1
                            if (download_batch_interval != 0) and (submitted % download_batch_size == 0):
                                progress_bar(submitted, total, f'<{table}>: Submitting tasks, '
                                                               f'Pausing for {download_batch_interval} sec...')
                                time.sleep(download_batch_interval)
                        # futures = {worker.submit(acquire_data, api_name, **kw): kw
                        #            for kw in all_kwargs}
                        progress_bar(0, total, f'<{table}>: estimating time left...')
                        for f in as_completed(futures):
                            df = f.result()
                            cur_kwargs = futures[f]
                            completed += 1
                            if completed % chunk_size:
                                dnld_data = pd.concat([dnld_data, df])
                            else:
                                dnld_data = pd.concat([dnld_data, df])
                                rows_affected = self.update_table_data(table, dnld_data)
                                dnld_data = pd.DataFrame()
                            total_written += rows_affected
                            time_elapsed = time.time() - st
                            time_remain = sec_to_duration((total - completed) * time_elapsed / completed,
                                                          estimation=True, short_form=False)
                            progress_bar(completed, total, f'<{table}:{list(cur_kwargs.values())[0]}>'
                                                           f'{total_written}wrtn/{time_remain} left')

                        total_written += self.update_table_data(table, dnld_data)
                else:
                    progress_bar(0, total, f'<{table}> estimating time left...')
                    for kwargs in all_kwargs:
                        df = self.fetch_history_table_data(table, channel='tushare', **kwargs)
                        completed += 1
                        if completed % chunk_size:
                            dnld_data = pd.concat([dnld_data, df])
                        else:
                            dnld_data = pd.concat([dnld_data, df])
                            rows_affected = self.update_table_data(table, dnld_data)
                            dnld_data = pd.DataFrame()
                        total_written += rows_affected
                        time_elapsed = time.time() - st
                        time_remain = sec_to_duration(
                                (total - completed) * time_elapsed / completed,
                                estimation=True,
                                short_form=False
                        )

                        if (download_batch_interval != 0) and (completed % download_batch_size == 0):
                            progress_bar(completed, total, f'<{table}:{list(kwargs.values())[0]}>'
                                                           f'{total_written}wrtn/Pausing for '
                                                           f'{download_batch_interval} sec...')
                            time.sleep(download_batch_interval)
                        else:
                            progress_bar(completed, total, f'<{table}:{list(kwargs.values())[0]}>'
                                                           f'{total_written}wrtn/{time_remain} left')
                    total_written += self.update_table_data(table, dnld_data)
                strftime_elapsed = sec_to_duration(
                        time_elapsed,
                        estimation=True,
                        short_form=True
                )
                if len(arg_coverage) > 1:
                    progress_bar(total, total, f'<{table}:{arg_coverage[0]}-{arg_coverage[-1]}>'
                                               f'{total_written}wrtn in {strftime_elapsed}\n')
                else:
                    progress_bar(total, total, f'[{table}:None>'
                                               f'{total_written}wrtn in {strftime_elapsed}\n')
            except Exception as e:
                total_written += self.update_table_data(table, dnld_data)
                msg = f'\n{str(e)}: \ndownload process interrupted at [{table}]:' \
                              f'<{arg_coverage[0]}>-<{arg_coverage[completed - 1]}>\n' \
                              f'{total_written} rows downloaded, will proceed with next table!'
                warnings.warn(msg)

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
        return df_s, df_i, df_f, df_ft, df_o

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
        import pymysql
        con = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.__user__,
                password=self.__password__,
                db=self.db_name,
        )
        try:
            con.ping(reconnect=True)
            con.ping()  # check if connection is still alive
            return True
        except Exception as e:
            print(f'{e} on {self.connection_type}, please check your connection')
            return False
        finally:
            con.close()

    # 真正的顶层数据获取API接口函数

    def get_data(self, htype, *, symbols=None, starts=None, ends=None, target_freq=None):
        """ DataSource类的最终输出方法，根据数据类型的获取方式，调用相应的方法获取数据并输出

        如果symbols为None，则输出为un-symbolised数据，否则输出为symbolised数据

        Parameters
        ----------
        htype: DataType
            数据类型对象
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        target_freq: str, optional
            用户要求的频率

        """

        acquisition_type = htype.acquisition_type
        kwargs = htype.kwargs

        if acquisition_type == 'basics':
            acquired_data = self._get_basics(symbols=symbols, **kwargs)
        elif acquisition_type == 'selection':
            acquired_data = self._get_selection(**kwargs)
        elif acquisition_type == 'direct':
            acquired_data = self._get_direct(symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'adjustment':
            acquired_data = self._get_adjustment(symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'operation':
            acquired_data = self._get_operation(symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'relations':
            acquired_data = self._get_relations(symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'event_multi_stat':
            acquired_data = self._get_event_multi_stat(symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'event_status':
            acquired_data = self._get_event_status(symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'event_signal':
            acquired_data = self._get_event_signal(symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'composition':
            acquired_data = self._get_composition(symbols=symbols, starts=starts, ends=ends, **kwargs)
        elif acquisition_type == 'category':
            acquired_data = self._get_category(symbols=symbols, **kwargs)
        elif acquisition_type == 'complex':
            acquired_data = self._get_complex(symbols=symbols, date=starts, **kwargs)
        else:
            raise ValueError(f'Unknown acquisition type: {acquisition_type}')

        if acquisition_type == 'basics':
            return acquired_data

        if acquired_data.empty:
            return acquired_data

        # adjust the time index frequency
        # acquired_freq = acquired_data.index.freq
        # if acquired_freq != htype.freq:
        #     raise RuntimeError("there's something wrong, the acquired freq should be the same as the data type's freq")

        if target_freq is not None and target_freq != htype.freq:
            acquired_data = self._adjust_freq(acquired_data, target_freq)

        if symbols is None:
            return self._unsymbolised(acquired_data)

        return self._symbolised(acquired_data)

    # 下面获取数据的方法都放在datasource中
    def _get_basics(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.Series:
        """基本数据的获取方法"""

        # try to get arguments from kwargs
        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        # if table_name == 'sw_industry_basic':
        #     import pdb; pdb.set_trace()

        if table_name is None or column is None:
            raise ValueError('table_name and column must be provided for basics data type')

        acquired_data = self.read_table_data(table_name, shares=symbols, start=starts, end=ends)

        if acquired_data.empty:
            return pd.Series()

        if column not in acquired_data.columns:
            raise KeyError(f'column {column} not in table data: {acquired_data.columns()}')

        return acquired_data[column]

    def _get_selection(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """数据筛选型的数据获取方法"""
        raise NotImplementedError

    def _get_direct(self, *, symbols, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """直读数据型的数据获取方法, 必须给出symbols"""
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for direct data type')

        data_series = self._get_basics(symbols=symbols, starts=starts, ends=ends, **kwargs)

        if data_series.empty:
            return pd.DataFrame()

        unstacked_df = data_series.unstack(level=0)

        return unstacked_df

    def _get_adjustment(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """数据修正型的数据获取方法"""
        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        adj_table = kwargs.get('adj_table')
        adj_column = kwargs.get('adj_column')
        adj_type = kwargs.get('adj_type')

        if table_name is None or column is None or adj_table is None or adj_column is None:
            raise ValueError(
                'table_name_A, column_A, table_name_B and column_B must be provided for adjustment data type')

        acquired_data = self.read_table_data(table_name, shares=symbols, start=starts, end=ends)
        acquired_data = acquired_data[column].unstack(level=0)

        adj_factors = self.read_table_data(adj_table, shares=symbols, start=starts, end=ends)
        adj_factors = adj_factors[adj_column].unstack(level=0)

        adj_factors = adj_factors.reindex(acquired_data.index, method='ffill')
        back_adj_data = acquired_data * adj_factors

        if adj_type == 'backward':
            return back_adj_data

        fwd_adj_data = back_adj_data / adj_factors.iloc[-1]
        return fwd_adj_data

    def _get_operation(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """数据操作型的数据获取方法"""
        raise NotImplementedError

    def _get_relations(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """数据关联型的数据获取方法"""
        raise NotImplementedError

    def _get_event_multi_stat(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """事件多状态型的数据获取方法

        Parameters
        ----------
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        **kwargs
            table_name: str
                数据表名
            column: str
                数据表中的列名
            id_index: str
                数据表中的id列名
            start_col: str
                数据表中的开始时间列名
            end_col: str
                数据表中的结束时间列名

        Returns
        -------
        DataFrame
        """

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        id_index = kwargs.get('id_index')
        start_col = kwargs.get('start_col')
        end_col = kwargs.get('end_col')

        if table_name is None or column is None:
            raise ValueError('table_name and column must be provided for basics data type')

        acquired_data = self.read_table_data(table_name, shares=symbols, start=starts, end=ends)
        columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table_name, with_primary_keys=True)
        acquired_data = set_primary_key_frame(acquired_data, primary_key=primary_keys, pk_dtypes=pk_dtypes)
        cols_to_keep = [start_col, end_col, column]
        cols_to_keep.extend(primary_keys)
        acquired_data = acquired_data[cols_to_keep]
        # create id_index and column pairs
        acquired_data[column] = acquired_data[id_index] + '-' + acquired_data[column].astype(str)

        if acquired_data.empty:
            return pd.DataFrame()

        # make group and combine events on the same date for the same symbol
        grouped = acquired_data.groupby(['ts_code', start_col])
        events = grouped[column].apply(lambda x: list(x))
        events = events.unstack(level=0)

        # expand the index to include starts and ends dates
        events = _expand_df_index(events, starts, ends).ffill()

        # filter out events that are not in the date range
        date_mask = (events.index >= starts) & (events.index <= ends)
        events = events.loc[date_mask]

        return events

    def _get_event_status(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """事件状态型的数据获取方法

        Parameters
        ----------
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        **kwargs
            table_name: str
                数据表名
            column: str
                数据表中的列名
            id_index: str
                数据表中的id列名
            start_col: str
                数据表中的开始时间列名
            end_col: str
                数据表中的结束时间列名

        Returns
        -------
        DataFrame
        """

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        # acquire data with out time thus status can be ffilled from previous dates
        data_series = self._get_basics(symbols=symbols, starts=None, ends=None, **kwargs)

        if data_series.empty:
            return pd.DataFrame()

        data_df = data_series.unstack(level='ts_code')

        # expand the index to include starts and ends dates
        status = _expand_df_index(data_df, starts, ends).ffill()

        # filter out events that are not in the date range
        date_mask = (status.index >= starts) & (status.index <= ends)
        status = status.loc[date_mask]

        return status

    def _get_event_signal(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """事件信号型的数据获取方法

        Parameters
        ----------
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        **kwargs
            table_name: str
                数据表名
            column: str
                数据表中的列名
            id_index: str
                数据表中的id列名
            start_col: str
                数据表中的开始时间列名
            end_col: str
                数据表中的结束时间列名

        Returns
        -------
        DataFrame
        """

        if symbols is None:
            raise ValueError('symbols must be provided for event status data type')
        if starts is None or ends is None:
            raise ValueError('start and end must be provided for event status data type')

        data_series = self._get_basics(symbols=symbols, starts=starts, ends=ends, **kwargs)

        if data_series.empty:
            return pd.DataFrame()

        signals = data_series.unstack(level='ts_code')

        return signals

    def _get_composition(self, *, symbols=None, starts=None, ends=None, **kwargs) -> pd.DataFrame:
        """成份查询型的数据获取方法

        Parameters
        ----------
        symbols: list
            股票代码列表
        starts: str
            开始日期
        ends: str
            结束日期
        **kwargs
            table_name: str
                数据表名
            column: str
                数据表中的列名
            comp_column: str
                数据表中的成份列名
            index: str
                数据表中的索引列名

        Returns
        -------
        DataFrame
        """

        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        comp_column = kwargs.get('comp_column')
        index = kwargs.get('index')

        weight_data = self.read_table_data(table_name, shares=index, start=starts, end=ends)
        if not weight_data.empty:
            weight_data = weight_data.unstack()
        else:
            # return empty data
            return weight_data

        weight_data.columns = weight_data.columns.get_level_values(1)
        weight_data.index = weight_data.index.get_level_values(1)

        if symbols is not None:
            weight_data = weight_data.reindex(columns=symbols)

        return weight_data

    def _get_category(self, *, symbols=None, **kwargs) -> pd.DataFrame:
        """成份查询型的数据获取方法

                Parameters
                ----------
                symbols: list
                    股票代码列表
                starts: str
                    开始日期
                ends: str
                    结束日期
                **kwargs
                    table_name: str
                        数据表名
                    column: str
                        数据表中的列名
                    comp_column: str
                        数据表中的成份列名
                    index: str
                        数据表中的索引列名

                Returns
                -------
                DataFrame
                """

        table_name = kwargs.get('table_name')
        column = kwargs.get('column')
        comp_column = kwargs.get('comp_column')

        category_data = self.read_table_data(table_name)
        category = category_data.index.to_frame()
        category.index = category[column]

        category = category.reindex(index=symbols)

        return category[comp_column]

    def _get_complex(self, *, symbols=None, date=None, **kwargs) -> pd.DataFrame:
        """复合型的数据获取方法"""
        raise NotImplementedError

    def _adjust_freq(self, acquired_data, freq) -> pd.DataFrame:
        """调整获取的数据的频率"""
        raise NotImplementedError

    def _symbolised(self, acquired_data) -> pd.DataFrame:
        """将数据转换为symbolised格式"""
        return acquired_data

    def _unsymbolised(self, acquired_data) -> pd.Series:
        """将数据转换为un-symbolised格式"""
        return acquired_data


# 以下是通用dataframe操作函数
def set_primary_key_index(df, primary_key, pk_dtypes):
    """ df是一个DataFrame，primary key是df的某一列或多列的列名，将primary key所指的
    列设置为df的行标签，设置正确的时间日期格式，并删除primary key列后返回新的df

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的DataFrame
    primary_key: list of str
        需要设置为行标签的列名，所有列名必须出现在df的列名中
    pk_dtypes: list of str
        需要设置为行标签的列的数据类型，日期数据需要小心处理

    Returns
    -------
    None
    """
    if not isinstance(df, pd.DataFrame):
        err = TypeError(f'df should be a pandas DataFrame, got {type(df)} instead')
        raise err
    if df.empty:
        return df
    if not isinstance(primary_key, list):
        err = TypeError(f'primary key should be a list, got {type(primary_key)} instead')
        raise err
    all_columns = df.columns
    if not all(item in all_columns for item in primary_key):
        err = KeyError(f'primary key contains invalid value: '
                       f'{[item for item in primary_key if item not in all_columns]}')
        raise err

    # 设置正确的时间日期格式(找到pk_dtype中是否有"date"或"TimeStamp"类型，将相应的列设置为TimeStamp
    set_datetime_format_frame(df, primary_key, pk_dtypes)

    # 设置正确的Index或MultiIndex
    pk_count = len(primary_key)
    if pk_count == 1:
        # 当primary key只包含一列时，创建single index
        df.index = df[primary_key[0]]
    elif pk_count > 1:
        # 当primary key包含多列时，创建MultiIndex
        m_index = pd.MultiIndex.from_frame(df[primary_key])
        df.index = m_index
    else:
        # for other unexpected cases
        err = ValueError(f'wrong input!')
        raise err
    df.drop(columns=primary_key, inplace=True)

    return None


def _resample_data(hist_data, target_freq,
                   method='last',
                   b_days_only=True,
                   trade_time_only=True,
                   forced_start=None,
                   forced_end=None,
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
        err = TypeError
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


# noinspection PyUnresolvedReferences
def set_primary_key_frame(df, primary_key, pk_dtypes):
    """ 与set_primary_key_index的功能相反，将index中的值放入DataFrame中，
        并重设df的index为0，1，2，3，4...

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的df
    primary_key: list
        primary key的名称
    pk_dtypes: list
        primary key的数据类型

    Returns
    -------
    df: pd.DataFrame

    Examples
    --------
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> df = set_primary_key_frame(df, ['a'], ['int'])
    >>> df
         a  b
    0    1  4
    1    2  5
    2    3  6
    >>> set_primary_key_index(df, ['a'], ['int'])
    >>> df
         b
    a
    1    4
    2    5
    3    6
    """

    if not isinstance(df, pd.DataFrame):
        err = TypeError(f'df should be a pandas DataFrame, got {type(df)} instead')
        raise err
    if df.empty:
        return df
    if not isinstance(primary_key, list):
        err = TypeError(f'primary key should be a list, got {type(primary_key)} instead')
        raise err
    if not isinstance(pk_dtypes, list):
        err = TypeError(f'primary key should be a list, got {type(primary_key)} instead')
        raise err

    all_columns = df.columns
    if not all(item in all_columns for item in primary_key):
        if not all(key in df.index.names for key in primary_key):
            msg = f'primary key contains invalid value: {[item for item in primary_key if item not in all_columns]}'
            raise KeyError(msg)

    idx_columns = list(df.index.names)
    pk_columns = primary_key

    if idx_columns != [None]:
        # index中有值，需要将index中的值放入DataFrame中
        index_frame = df.index.to_frame()
        for col in idx_columns:
            df[col] = index_frame[col]

    df.index = range(len(df))
    # 此时primary key有可能被放到了columns的最后面，需要将primary key移动到columns的最前面：
    columns = df.columns.to_list()
    new_col = [col for col in columns if col not in pk_columns]
    new_col = pk_columns + new_col
    df = df.reindex(columns=new_col, copy=False)

    # 设置正确的时间日期格式(找到pk_dtype中是否有"date"或"TimeStamp"类型，将相应的列设置为TimeStamp
    set_datetime_format_frame(df, primary_key, pk_dtypes)

    return df


def set_datetime_format_frame(df, primary_key: [str], pk_dtypes: [str]) -> None:
    """ 根据primary_key的rule为df的主键设置正确的时间日期类型

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的df
    primary_key: list of str
        主键列
    pk_dtypes: list of str
        主键数据类型，主要关注"date" 和"TimeStamp"

    Returns
    -------
    None

    Examples
    --------
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> df = set_primary_key_frame(df, ['a'], [int])
    >>> df
         a    b
    0    1    4
    1    2    5
    2    3    6
    >>> set_primary_key_index(df, ['a'], ['int'])
    >>> df
         b
    a
    1    4
    2    5
    3    6
    >>> set_datetime_format_frame(df, ['a'], ['date'])
    >>> df
                                     b
    a
    1970-01-01 00:00:00.000000001    4
    1970-01-01 00:00:00.000000002    5
    1970-01-01 00:00:00.000000003    6

    """
    # 设置正确的时间日期格式(找到pk_dtype中是否有"date", "datetime"或"TimeStamp"类型，将相应的列设置为TimeStamp
    datetime_dtypes = ['date', 'datetime', 'TimeStamp']

    if any(dtype in pk_dtypes for dtype in datetime_dtypes):
        # 需要设置正确的时间日期格式：
        # 有时候pk会包含多列，可能有多个时间日期，因此需要逐个设置
        for pk_item, dtype in zip(primary_key, pk_dtypes):
            if dtype in datetime_dtypes:
                df[pk_item] = pd.to_datetime(df[pk_item])
    return None


def get_primary_key_range(df, primary_key, pk_dtypes):
    """ 给定一个dataframe，给出这个df表的主键的范围，用于下载数据时用作传入参数
        如果主键类型为string，则给出一个list，包含所有的元素
        如果主键类型为date，则给出上下界

    Parameters
    ----------
    df: pd.DataFrame
        需要操作的df
    primary_key: list
        以列表形式给出的primary_key列名
    pk_dtypes: list
        primary_key的数据类型

    Returns
    -------
    dict，形式为{primary_key1: [values], 'start': start_date, 'end': end_date}

    # TODO: 下面的Example由Copilot生成，需要检查
    Examples
    --------
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> df
            a  b
    0    1    4
    1    2    5
    2    3    6
    >>> df = set_primary_key_index(df, ['a'], ['int'])
    >>> df
            b
    a
    1    4
    2    5
    3    6
    >>> get_primary_key_range(df, ['a'], ['int'])
    {'shares': [1, 2, 3]}
    >>> df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    >>> df = set_primary_key_frame(df, ['a'], ['date'])
    >>> df
            a  b
    0    1    4
    1    2    5
    2    3    6
    >>> df = set_primary_key_index(df, ['a'], ['date'])
    >>> df
            b
    a
    1970-01-01 00:00:00.000000001    4
    1970-01-01 00:00:00.000000002    5
    1970-01-01 00:00:00.000000003    6
    >>> get_primary_key_range(df, ['a'], ['date'])
    {'start': Timestamp('1970-01-01 00:00:00.000000001'), 'end': Timestamp('1970-01-01 00:00:00.000000003')}

    """
    if df.index.name is not None:
        df = set_primary_key_frame(df, primary_key=primary_key, pk_dtypes=pk_dtypes)
    res = {}
    for pk, dtype in zip(primary_key, pk_dtypes):
        if (dtype == 'str') or (dtype[:7] == 'varchar'):
            res['shares'] = (list(set(df[pk].values)))
        elif dtype.lower() in ['date', 'timestamp', 'datetime', 'int', 'float', 'double']:
            res['start'] = df[pk].min()
            res['end'] = df[pk].max()
        else:
            raise KeyError(f'invalid dtype: {dtype}')
    return res


def htype_to_table_col(htypes, freq='d', asset_type='E', method='permute', soft_freq=False):
    """ 根据输入的字符串htypes\freq\asset_type,查找包含该data_type的数据表以及column
        仅支持精确匹配。无法精确匹配数据表时，报错

    Parameters
    ----------
    htypes: str or list of str
        需要查找的的数据类型，该数据类型必须能在data_table_map中找到，包括所有内置数据类型，
        也包括自定义数据类型（自定义数据类型必须事先添加到data_table_map中），
        否则会被忽略
        当输入类型为str时，可以接受逗号分隔的字符串表示多个不同的data type
        如下面两种输入等效：
        'close, open, high' == ['close', 'open', 'high']
    freq: str or list of str default 'd'
        所需数据的频率，数据频率必须符合标准频率定义，即包含以下关键字：
        min / hour / H / d / w / M / Q / Y
        同时支持含数字或附加信息的频率如：
        5min / 2d / W-Fri
        如果输入的频率在data_table_map中无法找到，则根据soft_freq的值采取不同处理方式：
        - 如果soft_freq == True:
            在已有的data_table_map中查找最接近的freq并输出
        - 如果soft_freq == False:
            该项被忽略
    asset_type: (str, list) default 'E'
        所需数据的资产类型。该资产类型必须能在data_table_map中找到，
        否则会被忽略
        输入逗号分隔的多个asset_type等效于多个asset_type的list
    method: str
        决定htype和asset_type数据的匹配方式以及输出的数据表数量：
        - 'exact': 完全匹配，针对输入的每一个参数匹配一张数据表
          输出的数据列数量与htype/freq/asset_type的最大数量相同，
          如果输入的数据中freq与asset_type数量不足时，自动补足
          如果输入的数据中freq与asset_type数量太多时，自动忽略
          当输入的htype或asset_type中有一个或多个无法在data_table_map中找到匹配项时，该项会被忽略
        举例：
            输入为:
                ['close', 'pe'], ['d', 'd'], ['E', 'IDX'] 时，
            输出为:
                {'stock_daily':     ['close'],
                 'index_indicator': ['pe']}

        - 'permute': 排列组合，针对输入数据的排列组合输出匹配的数据表
          输出的数据列数量与htype/freq/asset_type的数量乘积相同，但同一张表中的数据列会
          被合并
          当某一个htype或asset_type的组合无法在data_table_map中找到时，忽略该组合
        举例：
            输入为:
                ['close', 'pe', 'open'], ['d'], ['E', 'IDX']时，
            输出为:
                {'stock_daily':     ['close', 'open'],
                 'index_daily':     ['close', 'open'],
                 'stock_indicator': ['pe'],
                 'index_indicator': ['pe']}
    soft_freq: bool, default False
        决定freq的匹配方式：
        - True: 允许不完全匹配输入的freq，优先查找更高且能够等分匹配的频率，
          失败时查找更低的频率，如果都失败，则输出None(当method为'exact'时)，
          或被忽略(当method为'permute'时)
        - False:不允许不完全匹配的freq，当输入的freq无法匹配时输出None(当method为'exact'时)

    Returns
    -------
    matched_tables: dict
    key为需要的数据所在数据表，value为该数据表中的数据列:
    {tables: columns}

    TODO: 未来可以考虑增加对freq的soft匹配，即允许不完全匹配输入的freq，优先查找更高且能够等分匹配的频率，
     失败时查找更低的频率，如果都失败，则输出None(当method为'exact'时)，
     或被忽略(当method为'permute'时)

    TODO: 下面Example中的输出结果需要更新
    Examples
    --------
    >>> htype_to_table_col('close, open, high', freq='d', asset_type='E', method='exact')
    {'stock_daily': ['close', 'open', 'high']}
    >>> htype_to_table_col('close, open, high', freq='d, m', asset_type='E', method='exact')
    {'stock_daily': ['close', 'high'], 'stock_monthly': ['open']}
    >>> htype_to_table_col('close, open, high', freq='d, m', asset_type='E, IDX', method='exact')
    {'index_monthly': ['open'], 'stock_daily': ['close', 'high']}
    >>> htype_to_table_col('close, open, high', freq='d, m', asset_type='E, IDX', method='permute')
    {'stock_daily': ['close', 'open', 'high'],
     'stock_monthly': ['close', 'open', 'high'],
     'index_daily': ['close', 'open', 'high'],
     'index_monthly': ['close', 'open', 'high']}
    """
    if isinstance(htypes, str):
        htypes = str_to_list(htypes)
    if isinstance(freq, str):
        freq = str_to_list(freq)
    if isinstance(asset_type, str):
        if asset_type.lower() == 'any':
            from .utilfuncs import AVAILABLE_ASSET_TYPES
            asset_type = AVAILABLE_ASSET_TYPES
        else:
            asset_type = str_to_list(asset_type)

    # 根据资产类型、数据类型和频率找到应该下载数据的目标数据表

    # 并开始从dtype_map中查找内容,
    # - exact模式下使用reindex确保找足数量，按照输入组合的数量查找，找不到的输出NaN
    # - permute模式下将dtype/freq/atype排列组合后查找所有可能的数据表，找不到的输出NaN
    dtype_map = get_dtype_map()
    if method.lower() == 'exact':
        # 一一对应方式，仅严格按照输入数据的数量一一列举数据表名称：
        idx_count = max(len(htypes), len(freq), len(asset_type))
        freq_padder = freq[0] if len(freq) == 1 else 'd'
        asset_padder = asset_type[0] if len(asset_type) == 1 else 'E'
        htypes = input_to_list(htypes, idx_count, padder=htypes[-1])
        freq = input_to_list(freq, idx_count, padder=freq_padder)
        asset_type = input_to_list(asset_type, idx_count, padder=asset_padder)
        dtype_idx = [(h, f, a) for h, f, a in zip(htypes, freq, asset_type)]

    elif method.lower() == 'permute':
        import itertools
        dtype_idx = list(itertools.product(htypes, freq, asset_type))

    else:  # for some unexpected cases
        raise KeyError(f'invalid method {method}')

    # 查找内容
    found_dtypes = dtype_map.reindex(index=dtype_idx)

    # 检查找到的数据中是否有NaN值，即未精确匹配到的值，确认是由于dtype/atype不对还是freq不对造成的
    # 如果是freq不对造成的，则需要抖动freq后重新匹配
    not_matched = found_dtypes.isna().all(axis=1)
    all_found = ~not_matched.any()  # 如果没有任何组合未找到，等价于全部组合都找到了
    # 在soft_freq模式下，进一步确认无法找到数据的原因，如果因为freq不匹配，则抖动freq后重新查找
    rematched_tables = {}
    if (not all_found) and soft_freq:
        # 有部分htype/freq/type组合没有找到结果，这部分index需要调整
        unmatched_index = found_dtypes.loc[not_matched].index
        unmatched_dtypes = [item[0] for item in unmatched_index]
        unmatched_freqs = [item[1] for item in unmatched_index]
        unmatched_atypes = [item[2] for item in unmatched_index]
        map_index = dtype_map.index
        all_dtypes = map_index.get_level_values(0)
        all_freqs = map_index.get_level_values(1)
        all_atypes = map_index.get_level_values(2)

        rematched_dtype_index = []
        for dt, fr, at in zip(unmatched_dtypes, unmatched_freqs, unmatched_atypes):
            try:
                rematched_dtype_loc = all_dtypes.get_loc(dt)
                rematched_atype_loc = all_atypes.get_loc(at)
            except KeyError:
                # 如果产生Exception，说明dt或at无法精确匹配
                # 此时应该保留全NaN输出
                continue
                # raise KeyError(f'dtype ({dt}) or asset_type ({at}) can not be found in dtype map')
            # 否则就是freq无法精确匹配，此时需要抖动freq
            '''
            原本使用下面的方法获取同时满足两个条件的freq的集合
            available_freq_list = all_freqs[rematched_dtype_loc & rematched_atype_loc]
            available_freq_list = list(set(available_freq_list))
            但是rematched_dtype_loc和rematched_atype_loc有时候类型不同，因此无法直接&
            例如，当dt = invest_income 时，rematched_dtype_loc返回值为一个数字209，
            而当at = E 时，rematched_atype_loc返回值为一个bool series
            两者无法直接进行 & 运算，因此会导致错误结果
            因此直接使用集合交集运算
            '''
            dtype_freq_list = set(all_freqs[rematched_dtype_loc])
            atype_freq_list = set(all_freqs[rematched_atype_loc])
            available_freq_list = list(dtype_freq_list.intersection(atype_freq_list))

            # 当无法找到available freq list时，跳过这一步
            if len(available_freq_list) == 0:
                continue

            dithered_freq = freq_dither(fr, available_freq_list)
            # 将抖动后生成的新的dtype ID保存下来
            rematched_dtype_index.append((dt, dithered_freq.lower(), at))

        # 抖动freq后生成的index中可能有重复项，需要去掉重复项
        rematched_dtype_index_unduplicated = list(set(rematched_dtype_index))
        # 通过去重后的index筛选出所需的dtypes
        rematched_dtypes = dtype_map.reindex(index=rematched_dtype_index_unduplicated)
        # 合并成组后生成dict
        group = rematched_dtypes.groupby(['table_name'])
        rematched_tables = group['column'].apply(list).to_dict()

    # 从found_dtypes中提取数据并整理为dict
    group = found_dtypes.groupby(['table_name'])
    matched_tables = group['column'].apply(list).to_dict()

    if soft_freq:
        # 将找到的dtypes与重新匹配的dtypes合并
        matched_tables.update(rematched_tables)
    return matched_tables


# noinspection PyTypeChecker
@lru_cache(maxsize=16)
def get_built_in_table_schema(table, *, with_remark=False, with_primary_keys=True) -> tuple:
    """ 给出数据表的名称，从相关TABLE中找到表的主键名称及其数据类型

    Parameters
    ----------
    table:
        str, 表名称(注意不是表的结构名称)
    with_remark: bool
        为True时返回remarks，否则不返回
    with_primary_keys: bool
        为True时返回primary_keys以及primary_key的数据类型，否则不返回

    Returns
    -------
    Tuple: 包含四个List，包括:
        columns: 整张表的列名称
        dtypes: 整张表所有列的数据类型
        primary_keys: 主键列名称
        pk_dtypes: 主键列的数据类型
    """
    if not isinstance(table, str):
        err = TypeError(f'table name should be a string, got {type(table)} instead')
        raise err
    if table not in TABLE_MASTERS.keys():
        raise KeyError(f'invalid table name')

    table_schema = TABLE_MASTERS[table][TABLE_MASTER_COLUMNS.index('schema')]
    schema = TABLE_SCHEMA[table_schema]
    columns = schema['columns']
    dtypes = schema['dtypes']
    remarks = schema['remarks']
    pk_loc = schema['prime_keys']
    primary_keys = [columns[i] for i in pk_loc]
    pk_dtypes = [dtypes[i] for i in pk_loc]

    if (not with_remark) and with_primary_keys:
        return columns, dtypes, primary_keys, pk_dtypes
    if with_remark and (not with_primary_keys):
        return columns, dtypes, remarks
    if (not with_remark) and (not with_primary_keys):
        return columns, dtypes
    if with_remark and with_primary_keys:
        return columns, dtypes, remarks, primary_keys, pk_dtypes


@lru_cache(maxsize=1)
def get_dtype_map() -> pd.DataFrame:
    """ 获取所有内置数据类型的清单

    Returns
    -------
    dtype_map: pd.DataFrame

    """
    dtype_map = pd.DataFrame(DATA_TYPE_MAP).T
    dtype_map.columns = DATA_TYPE_MAP_COLUMNS
    dtype_map.index.names = DATA_TYPE_MAP_INDEX_NAMES
    return dtype_map


@lru_cache(maxsize=1)
def get_table_map() -> pd.DataFrame:  # deprecated
    """ 获取所有内置数据表的清单，to be deprecated

    Returns
    -------
    pd.DataFrame
    数据表清单
    """
    warnings.warn('get_table_map() is deprecated, use get_table_master() instead', DeprecationWarning)
    return get_table_master()


@lru_cache(maxsize=1)
def get_table_master() -> pd.DataFrame:
    """ 获取所有内置数据表的清单

    Returns
    -------
    table_masters: pd.DataFrame
    数据表清单, 包含以下字段:
    """
    table_master = pd.DataFrame(TABLE_MASTERS).T
    table_master.columns = TABLE_MASTER_COLUMNS
    return table_master


def find_history_data(s, match_description=False, fuzzy=False, freq=None, asset_type=None, match_threshold=0.85):
    """ 根据输入的字符串，查找或匹配历史数据类型,并且显示该历史数据的详细信息。支持模糊查找、支持通配符、支持通过英文字符或中文
    查找匹配的历史数据类型。

    Parameters
    ----------
    s: str
        一个字符串，用于查找或匹配历史数据类型
    match_description: bool, Default: False
        是否模糊匹配数据描述，如果给出的字符串中含有非Ascii字符，会自动转为True
         - False: 仅匹配数据名称
         - True:  同时匹配数据描述
    fuzzy: bool, Default: False
        是否模糊匹配数据名称，如果给出的字符串中含有非Ascii字符或通配符*/?，会自动转为True
         - False: 精确匹配数据名称
         - True:  模糊匹配数据名称或数据描述
    freq: str, Default: None
        数据频率，如果提供，则只匹配该频率的数据
        可以输入单个频率，也可以输入逗号分隔的多个频率
    asset_type: str, Default: None
        证券类型，如果提供，则只匹配该证券类型的数据
        可以输入单个证券类型，也可以输入逗号分隔的多个证券类型
    match_threshold: float, default 0.85
        匹配度阈值，匹配度超过该阈值的项目会被判断为匹配

    Returns
    -------
    data_id: list
        匹配到的数据类型的data_id，可以用于qt.get_history_data()下载数据

    Examples
    --------
    >>> import qteasy as qt
    >>> qt.find_history_data('pe')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its data_id:
    ------------------------------------------------------------------------
               freq asset             table                            desc
    data_id
    initial_pe    d     E         new_share                  新股上市信息 - 发行市盈率
    pe            d   IDX   index_indicator                    指数技术指标 - 市盈率
    pe            d     E   stock_indicator  股票技术指标 - 市盈率（总市值/净利润， 亏损的PE为空）
    pe_2          d     E  stock_indicator2                  股票技术指标 - 动态市盈率
    ========================================================================

    >>> qt.find_history_data('ep*')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its data_id:
    ------------------------------------------------------------------------
                  freq asset      table                 desc
    data_id
    eps_last_year    q     E    express  上市公司业绩快报 - 去年同期每股收益
    eps              q     E  financial    上市公司财务指标 - 基本每股收益
    ========================================================================

    >>> qt.find_history_data('每股收益')
    matched following history data,
    use "qt.get_history_data()" to load these historical data by its data_id:
    ------------------------------------------------------------------------
                    freq asset      table                 desc
    data_id
    basic_eps              q     E     income           上市公司利润表 - 基本每股收益
    diluted_eps            q     E     income           上市公司利润表 - 稀释每股收益
    express_diluted_eps    q     E    express     上市公司业绩快报 - 每股收益(摊薄)(元)
    yoy_eps                q     E    express    上市公司业绩快报 - 同比增长率:基本每股收益
    eps_last_year          q     E    express        上市公司业绩快报 - 去年同期每股收益
    eps                    q     E  financial          上市公司财务指标 - 基本每股收益
    dt_eps                 q     E  financial          上市公司财务指标 - 稀释每股收益
    diluted2_eps           q     E  financial        上市公司财务指标 - 期末摊薄每股收益
    q_eps                  q     E  financial       上市公司财务指标 - 每股收益(单季度)
    basic_eps_yoy          q     E  financial  上市公司财务指标 - 基本每股收益同比增长率(%)
    dt_eps_yoy             q     E  financial  上市公司财务指标 - 稀释每股收益同比增长率(%)
    ========================================================================

    Raises
    ------
    TypeError: 输入的s不是字符串，或者freq/asset_type不是字符串或列表
    """

    if not isinstance(s, str):
        err = TypeError(f'input should be a string, got {type(s)} instead.')
        raise err
    # 判断输入是否ascii编码，如果是，匹配数据名称，否则，匹配数据描述
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        # is_ascii = False, 此时强制匹配description, 并且fuzzy匹配
        match_description = True
        fuzzy = True
    if match_description:
        fuzzy = True
    if ('?' in s) or ('*' in s):
        fuzzy = True  # 给出通配符时强制fuzzy匹配

    data_table_map = get_dtype_map()
    data_table_map['freq'] = data_table_map.index.get_level_values(level=1)
    data_table_map['asset_type'] = data_table_map.index.get_level_values(level=2)

    if freq is not None:
        if isinstance(freq, str):
            freq = str_to_list(freq)
        if not isinstance(freq, list):
            err = TypeError(f'freq should be a string or a list, got {type(freq)} instead')
            raise err
        data_table_map = data_table_map.loc[data_table_map['freq'].isin(freq)]
    if asset_type is not None:
        if isinstance(asset_type, str):
            asset_type = str_to_list(asset_type)
        if not isinstance(asset_type, list):
            err = TypeError(f'asset_type should be a string or a list, got {type(asset_type)} instead')
            raise err
        data_table_map = data_table_map.loc[data_table_map['asset_type'].isin(asset_type)]

    data_table_map['n_matched'] = 0  # name列的匹配度，模糊匹配的情况下，匹配度为0～1之间的数字
    data_table_map['d_matched'] = 0  # description列的匹配度，模糊匹配的情况下，匹配度为0～1之间的数字

    if (not fuzzy) and (not match_description):
        data_table_map['n_matched'] = data_table_map['column'] == s
        data_table_map['n_matched'] = data_table_map['n_matched'].astype('int')
    else:
        if match_description:
            where_to_look = ['column', 'description']
            match_how = [_lev_ratio, _partial_lev_ratio]
            result_columns = ['n_matched', 'd_matched']
        elif fuzzy:
            where_to_look = ['column']
            match_how = [_partial_lev_ratio]
            result_columns = ['n_matched']
        else:
            where_to_look = ['column']
            match_how = [_lev_ratio]
            result_columns = ['n_matched']

        for where, how, res in zip(where_to_look, match_how, result_columns):
            if ('?' in s) or ('*' in s):
                matched = _wildcard_match(s, data_table_map[where])
                match_values = [1 if item in matched else 0 for item in data_table_map[where]]
            else:
                match_values = list(map(how, [s] * len(data_table_map[where]), data_table_map[where]))
            data_table_map[res] = match_values

    data_table_map['matched'] = data_table_map['n_matched'] + data_table_map['d_matched']
    data_table_map = data_table_map.loc[data_table_map['matched'] >= match_threshold]
    data_table_map.drop(columns=['n_matched', 'd_matched', 'matched'], inplace=True)
    data_table_map.index = data_table_map.index.get_level_values(level=0)
    data_table_map.index.name = 'data_id'
    print(f'matched following history data, \n'
          f'use "qt.get_history_data()" to load these historical data by its data_id:\n'
          f'------------------------------------------------------------------------')
    print(
            data_table_map.to_string(
                    columns=['freq',
                             'asset_type',
                             'table_name',
                             'description'],
                    header=['freq',
                            'asset',
                            'table',
                            'desc'],
            )
    )
    print(f'========================================================================')
    return list(data_table_map.index)


def ensure_sys_table(table: str) -> None:
    """ 检察table是不是sys表

    Parameters
    ----------
    table: str
        表名称

    Returns
    -------
    None

    Raises
    ------
    KeyError: 当输入的表名称不正确时，或筛选条件字段名不存在时
    TypeError: 当输入的表名称类型不正确，或表使用方式不是sys类型时
    """

    # 检察输入的table名称，以及是否属于sys表
    if not isinstance(table, str):
        err = TypeError(f'table name should be a string, got {type(table)} instead.')
        raise err
    try:
        table_usage = TABLE_MASTERS[table][2]
        if not table_usage == 'sys':
            err = TypeError(f'Table {table}<{table_usage}> is not subjected to sys use')
            raise err
    except KeyError as e:
        raise KeyError(f'"{e}" is not a valid table name')
    except Exception as e:
        err = RuntimeError(f'{e}: An error occurred when checking table usage')
        raise err


def _expand_df_index(df: pd.DataFrame, starts: str, ends: str) -> pd.DataFrame:
    """将DataFrame的索引扩展到包含开始和结束日期"""

    starts = pd.to_datetime(starts)
    ends = pd.to_datetime(ends)

    df.index = pd.to_datetime(df.index)
    expanded_index = df.index.to_list()
    if starts not in expanded_index:
        expanded_index.append(starts)
    if ends not in expanded_index:
        expanded_index.append(ends)
    return df.reindex(expanded_index).sort_index(ascending=True)
