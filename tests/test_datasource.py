# coding=utf-8
# ======================================
# File:     test_datasource.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all local data source
#   related functions.
# ======================================
import unittest

import os
import qteasy as qt
import pandas as pd
from pandas import Timestamp
import numpy as np
from pymysql import connect

from qteasy.utilfuncs import str_to_list
from qteasy.trading_util import _trade_time_index

from qteasy.database import DataSource, set_primary_key_index, set_primary_key_frame
from qteasy.database import get_primary_key_range, htype_to_table_col
from qteasy.database import _resample_data, freq_dither
from qteasy.utilfuncs import get_main_freq_level, next_main_freq, parse_freq_string


# noinspection SqlDialectInspection,PyTypeChecker
class TestDataSource(unittest.TestCase):
    """test local historical f`~`ile database management methods"""

    def setUp(self):
        """ execute before each test"""
        from qteasy import QT_ROOT_PATH
        self.qt_root_path = QT_ROOT_PATH
        self.data_test_dir = 'data_test/'
        # 测试数据不会放在默认的data路径下，以免与已有的文件混淆
        # 使用测试数据库进行除"test_get_history_panel()"以外的其他全部测试
        # TODO: do not explicitly leave password and user in the code
        from qteasy import QT_CONFIG

        self.ds_db = DataSource(
                'db',
                host=QT_CONFIG['test_db_host'],
                port=QT_CONFIG['test_db_port'],
                user=QT_CONFIG['test_db_user'],
                password=QT_CONFIG['test_db_password'],
                db_name=QT_CONFIG['test_db_name']
        )
        self.ds_csv = DataSource('file', file_type='csv', file_loc=self.data_test_dir)
        self.ds_hdf = DataSource('file', file_type='hdf', file_loc=self.data_test_dir)
        self.ds_fth = DataSource('file', file_type='fth', file_loc=self.data_test_dir)
        self.df = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ'],
            'trade_date': ['20211112', '20211112', '20211112', '20211112', '20211112',
                           '20211113', '20211113', '20211113', '20211113', '20211113'],
            'open':       [1., 2., 3., 4., 5., 6., 7., 8., 9., 10.],
            'high':       [2., 3., 4., 5., 6., 7., 8., 9., 10., 1.],
            'low':        [3., 4., 5., 6., 7., 8., 9., 10., 1., 2.],
            'close':      [4., 5., 6., 7., 8., 9., 10., 1., 2., 3.]
        })
        # 以下df_add中的数据大部分主键与df相同，但有四行不同，且含有NaN与None值主键与df相同的行数据与df不同，用于测试新增及更新
        self.df_add = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000002.SZ', '000003.SZ', '000006.SZ', '000007.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000006.SZ', '000007.SZ'],
            'trade_date': ['20211112', '20211112', '20211112', '20211112', '20211112',
                           '20211113', '20211113', '20211113', '20211113', '20211113'],
            'open':       [10., 10., 10., None, 10., 10., 10., 10., 10., 10.],
            'high':       [10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'low':        [10., 10., 10., 10., 10., np.nan, 10., 10., 10., 10.],
            'close':      [10., 10., 10., 10., 10., 10., np.nan, 10., 10., 10.]
        })
        # 以下df_res中的数据是更新后的结果
        self.df_res = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000001.SZ', '000002.SZ', '000002.SZ', '000003.SZ', '000003.SZ', '000004.SZ',
                           '000004.SZ', '000005.SZ', '000005.SZ', '000006.SZ', '000006.SZ', '000007.SZ', '000007.SZ'],
            'trade_date': ['20211112', '20211113', '20211112', '20211113', '20211112', '20211113', '20211112',
                           '20211113', '20211112', '20211113', '20211112', '20211113', '20211112', '20211113'],
            'open':       [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 4.0, 9.0, 5.0, 10.0, np.nan, 10.0, 10.0, 10.0],
            'high':       [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 5.0, 10.0, 6.0, 1.0, 10.0, 10.0, 10.0, 10.0],
            'low':        [10.0, np.nan, 10.0, 10.0, 10.0, 10.0, 6.0, 1.0, 7.0, 2.0, 10.0, 10.0, 10.0, 10.0],
            'close':      [10.0, 10.0, 10.0, np.nan, 10.0, 10.0, 7.0, 2.0, 8.0, 3.0, 10.0, 10.0, 10.0, 10.0]
        })
        self.df2 = pd.DataFrame({
            'ts_code':  ['000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                         '000006.SZ', '000007.SZ', '000008.SZ', '000009.SZ', '000010.SZ'],
            'name':     ['name1', 'name2', 'name3', 'name4', 'name5', 'name6', 'name7', 'name8', 'name9', 'name10'],
            'industry': ['industry1', 'industry2', 'industry3', 'industry4', 'industry5',
                         'industry6', 'industry7', 'industry8', 'industry9', 'industry10'],
            'area':     ['area1', 'area2', 'area3', 'area4', 'area5', 'area6', 'area7', 'area8', 'area9', 'area10'],
            'market':   ['market1', 'market2', 'market3', 'market4', 'market5',
                         'market6', 'market7', 'market8', 'market9', 'market10']
        })
        # 以下df用于测试写入/读出/新增修改系统内置标准数据表
        self.built_in_df = pd.DataFrame({
            'ts_code':    ['000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ'],
            'trade_date': ['20211112', '20211112', '20211112', '20211112', '20211112',
                           '20211113', '20211113', '20211113', '20211113', '20211113',
                           '20211114', '20211114', '20211114', '20211114', '20211114'],
            'open':       [1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 6., 7., 8., 9., 10.],
            'high':       [2., 3., 4., 5., 6., 7., 8., 9., 10., 1., 7., 8., 9., 10., 1.],
            'low':        [3., 4., 5., 6., 7., 8., 9., 10., 1., 2., 8., 9., 10., 1., 2.],
            'close':      [4., 5., 6., 7., 8., 9., 10., 1., 2., 3., 9., 10., 1., 2., 3.],
            'pre_close':  [1., 2., 3., 4., 5., 6., 7., 8., 9., 10., 6., 7., 8., 9., 10.],
            'change':     [2., 3., 4., 5., 6., 7., 8., 9., 10., 1., 7., 8., 9., 10., 1.],
            'pct_chg':    [3., 4., 5., 6., 7., 8., 9., 10., 1., 2., 8., 9., 10., 1., 2.],
            'vol':        [4., 5., 6., 7., 8., 9., 10., 1., 2., 3., 9., 10., 1., 2., 3.],
            'amount':     [4., 5., 6., 7., 8., 9., 10., 1., 2., 3., 9., 10., 1., 2., 3.]
        })
        # 以下df用于测试新增数据写入/读出系统内置标准数据表，与第一次写入表中的数据相比，部分数据的
        # 主键与第一次相同，大部分主键不同。主键相同的数据中，价格与原来的值不同。
        # 正确的输出应该确保写入本地表的数据中不含重复的主键，用户可以选择用新的数据替换已有数据，或
        # 者忽略新的数据
        self.built_in_add_df = pd.DataFrame({
            'ts_code':    ['000006.SZ', '000007.SZ', '000008.SZ', '000004.SZ', '000005.SZ',
                           '000006.SZ', '000007.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                           '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ'],
            'trade_date': ['20211115', '20211115', '20211115', '20211115', '20211115',
                           '20211116', '20211116', '20211116', '20211116', '20211116',
                           '20211114', '20211114', '20211114', '20211114', '20211114'],
            'open':       [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'high':       [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'low':        [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'close':      [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'pre_close':  [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'change':     [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'pct_chg':    [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'vol':        [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.],
            'amount':     [10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10., 10.]
        })

    def test_properties(self):
        """test properties"""
        self.assertEqual(self.ds_csv.__str__(), 'file://csv@qt_root/data_test/')
        self.assertEqual(self.ds_hdf.__str__(), 'file://hdf@qt_root/data_test/')
        self.assertEqual(self.ds_fth.__str__(), 'file://fth@qt_root/data_test/')
        self.assertEqual(self.ds_db.__str__(), 'db:mysql://localhost@3306/test_db')

        self.assertEqual(self.ds_csv.__repr__(), "DataSource('file', 'csv', 'data_test/')")
        self.assertEqual(self.ds_hdf.__repr__(), "DataSource('file', 'hdf', 'data_test/')")
        self.assertEqual(self.ds_fth.__repr__(), "DataSource('file', 'fth', 'data_test/')")
        self.assertEqual(self.ds_db.__repr__(), "DataSource('db', 'localhost', 3306)")

        self.assertEqual(self.ds_csv.tables, [])
        self.assertEqual(self.ds_hdf.tables, [])
        self.assertEqual(self.ds_fth.tables, [])
        self.assertEqual(self.ds_db.tables, [])

    def test_primary_key_manipulate(self):
        """ test manipulating DataFrame primary key as indexes and frames
            with testing functions:
                set_primary_key_index() and,
                set_primary_key_frame()
        """
        print(f'df before converting primary keys to index:\n{self.df}')
        set_primary_key_index(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'date'])

        print(f'df after converting primary keys to index:\n{self.df}')
        self.assertEqual(list(self.df.index.names), ['ts_code', 'trade_date'])
        self.assertEqual(self.df.index[0], ('000001.SZ', Timestamp('2021-11-12 00:00:00')))
        self.assertEqual(self.df.columns.to_list(), ['open', 'high', 'low', 'close'])

        res = set_primary_key_frame(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'date'])
        print(f'df after converting primary keys to frame:\n{res}')
        self.assertEqual(list(res.index.names), [None])
        self.assertEqual(res.ts_code[0], '000001.SZ')
        self.assertEqual(res.trade_date[0], Timestamp('2021-11-12 00:00:00'))
        self.assertEqual(res.columns.to_list(), ['ts_code', 'trade_date', 'open', 'high', 'low', 'close'])

        print(f'df2 before converting primary keys to index:\n{self.df2}')
        set_primary_key_index(self.df2, primary_key=['ts_code'], pk_dtypes=['str'])

        print(f'df2 after converting primary keys to index:\n{self.df2}')
        self.assertEqual(list(self.df2.index.names), ['ts_code'])
        self.assertEqual(self.df2.index[0], '000001.SZ')
        self.assertEqual(self.df2.columns.to_list(), ['name', 'industry', 'area', 'market'])

        res = set_primary_key_frame(self.df2, primary_key=['ts_code'], pk_dtypes=['str'])
        print(f'df2 after converting primary keys to frame:\n{res}')
        self.assertEqual(list(res.index.names), [None])
        self.assertEqual(res.ts_code[0], '000001.SZ')
        self.assertEqual(res.columns.to_list(), ['ts_code', 'name', 'industry', 'area', 'market'])

        # test get_primary_key_range
        res = get_primary_key_range(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'date'])
        print(f'get primary key range of df:\n{res}')
        self.assertIsInstance(res, dict)
        self.assertTrue(all(item in ['000004.SZ', '000002.SZ', '000005.SZ', '000003.SZ', '000001.SZ'] for
                            item in res['shares']))
        self.assertEqual(res['start'], pd.to_datetime('20211112'))
        self.assertEqual(res['end'], pd.to_datetime('20211113'))

        res = get_primary_key_range(self.df2, primary_key=['ts_code'], pk_dtypes=['str'])
        print(f'get primary key range of df:\n{res}')
        target_list = ['000001.SZ', '000002.SZ', '000003.SZ', '000005.SZ', '000009.SZ',
                       '000006.SZ', '000008.SZ', '000004.SZ', '000007.SZ', '000010.SZ']
        self.assertIsInstance(res, dict)
        self.assertTrue(all(item in target_list for item in res['shares']))

    def test_datasource_creation(self):
        """ test creation of all kinds of arr sources"""
        self.assertIsInstance(self.ds_db, DataSource)
        self.assertEqual(self.ds_db.connection_type, 'db:mysql://localhost@3306/test_db')
        self.assertIs(self.ds_db.file_path, None)

        self.assertIsInstance(self.ds_csv, DataSource)
        self.assertEqual(self.ds_csv.connection_type, 'file://csv@qt_root/data_test/')
        self.assertEqual(self.ds_csv.file_type, 'csv')
        self.assertEqual(self.ds_csv.file_path, os.path.join(self.qt_root_path, 'data_test/'))

        self.assertIsInstance(self.ds_hdf, DataSource)
        self.assertEqual(self.ds_hdf.connection_type, 'file://hdf@qt_root/data_test/')
        self.assertEqual(self.ds_hdf.file_type, 'hdf')
        self.assertEqual(self.ds_hdf.file_path, os.path.join(self.qt_root_path, 'data_test/'))

        self.assertIsInstance(self.ds_fth, DataSource)
        self.assertEqual(self.ds_fth.connection_type, 'file://fth@qt_root/data_test/')
        self.assertEqual(self.ds_fth.file_type, 'fth')
        self.assertEqual(self.ds_fth.file_path, os.path.join(self.qt_root_path, 'data_test/'))

    def test_file_manipulates(self):
        """ test DataSource method file_exists and drop_file"""
        print(f'returning True while source type is database')
        self.assertRaises(RuntimeError, self.ds_db.file_exists, 'basic_eps.dat')

        print(f'test file that existed')
        f_name = self.ds_csv.file_path + 'test_file.csv'
        with open(f_name, 'w') as f:
            f.write('a test csv file')
        self.assertTrue(self.ds_csv.file_exists('test_file'))
        self.ds_csv.drop_file('test_file')
        self.assertFalse(self.ds_csv.file_exists('test_file'))

        f_name = self.ds_hdf.file_path + 'test_file.hdf'
        with open(f_name, 'w') as f:
            f.write('a test csv file')
        self.assertTrue(self.ds_hdf.file_exists('test_file'))
        self.ds_hdf.drop_file('test_file')
        self.assertFalse(self.ds_hdf.file_exists('test_file'))

        f_name = self.ds_fth.file_path + 'test_file.fth'
        with open(f_name, 'w') as f:
            f.write('a test csv file')
        self.assertTrue(self.ds_fth.file_exists('test_file'))
        self.ds_fth.drop_file('test_file')
        self.assertFalse(self.ds_fth.file_exists('test_file'))

        print(f'test file that does not exist')
        # 事先删除可能存在于磁盘上的文件，并判断是否存在
        import os
        f_name = self.ds_csv.file_path + "file_that_does_not_exist.csv"
        try:
            os.remove(f_name)
        except Exception:
            pass
        f_name = self.ds_hdf.file_path + "file_that_does_not_exist.hdf"
        try:
            os.remove(f_name)
        except Exception:
            pass
        f_name = self.ds_fth.file_path + "file_that_does_not_exist.fth"
        try:
            os.remove(f_name)
        except Exception:
            pass
        self.assertFalse(self.ds_csv.file_exists('file_that_does_not_exist'))
        self.assertFalse(self.ds_hdf.file_exists('file_that_does_not_exist'))
        self.assertFalse(self.ds_fth.file_exists('file_that_does_not_exist'))

    def test_db_table_operates(self):
        """ test all database operation functions"""
        self.ds_db.drop_db_table('new_test_table')
        self.assertFalse(self.ds_db.db_table_exists('new_test_table'))

        print(f'test function creating new table')
        self.ds_db.new_db_table('new_test_table',
                                ['ts_code', 'trade_date', 'col1', 'col2'],
                                ['varchar(9)', 'varchar(9)', 'int', 'int'],
                                ['ts_code', 'trade_date'])
        self.ds_db.db_table_exists('new_test_table')

        con = connect(
                host=self.ds_db.host,
                port=self.ds_db.port,
                user=self.ds_db.__user__,
                password=self.ds_db.__password__,
                db=self.ds_db.db_name,
        )
        cursor = con.cursor()
        sql = f"SELECT COLUMN_NAME, DATA_TYPE " \
              f"FROM INFORMATION_SCHEMA.COLUMNS " \
              f"WHERE TABLE_SCHEMA = Database() " \
              f"AND table_name = 'new_test_table'" \
              f"ORDER BY ordinal_position"
        cursor.execute(sql)
        results = cursor.fetchall()
        # 为了方便，将cur_columns和new_columns分别包装成一个字典
        test_columns = {}
        for col, typ in results:
            test_columns[col] = typ
        self.assertEqual(list(test_columns.keys()), ['ts_code', 'trade_date', 'col1', 'col2'])
        self.assertEqual(list(test_columns.values()), ['varchar', 'varchar', 'int', 'int'])

        self.ds_db.drop_db_table('new_test_table')

    def test_write_and_read_file(self):
        """ test DataSource method write_file and read_file"""
        print(f'write and read a MultiIndex dataframe to all types of local sources')
        df = set_primary_key_frame(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'TimeStamp'])
        set_primary_key_index(df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'TimeStamp'])
        print(f'following dataframe with multiple index will be written to disk in all formats:\n'
              f'{df}')
        self.ds_csv.write_file(df, 'test_csv_file')
        self.assertTrue(self.ds_csv.file_exists('test_csv_file'))
        loaded_df = self.ds_csv.read_file('test_csv_file',
                                          primary_key=['ts_code', 'trade_date'],
                                          pk_dtypes=['str', 'TimeStamp'])
        target_index = df.index.values
        loaded_index = loaded_df.index.values
        target_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved csv file is\n'
              f'{loaded_df}\n')
        for i in range(len(target_index)):
            self.assertEqual(target_index[i], loaded_index[i])
        self.assertTrue(np.allclose(target_values, loaded_values))
        self.assertEqual(list(df.columns), list(loaded_df.columns))

        self.ds_hdf.write_file(df, 'test_hdf_file')
        self.assertTrue(self.ds_hdf.file_exists('test_hdf_file'))
        loaded_df = self.ds_hdf.read_file('test_hdf_file',
                                          primary_key=['ts_code', 'trade_date'],
                                          pk_dtypes=['str', 'TimeStamp'])
        target_index = df.index.values
        loaded_index = loaded_df.index.values
        target_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved hdf file is\n'
              f'{loaded_df}\n')
        for i in range(len(target_index)):
            self.assertEqual(target_index[i], loaded_index[i])
        self.assertTrue(np.allclose(target_values, loaded_values))
        self.assertEqual(list(df.columns), list(loaded_df.columns))

        self.ds_fth.write_file(df, 'test_fth_file')
        self.assertTrue(self.ds_fth.file_exists('test_fth_file'))
        loaded_df = self.ds_fth.read_file('test_fth_file',
                                          primary_key=['ts_code', 'trade_date'],
                                          pk_dtypes=['str', 'TimeStamp'])
        target_index = df.index.values
        loaded_index = loaded_df.index.values
        target_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved feather file is\n'
              f'{loaded_df}\n')
        for i in range(len(target_index)):
            self.assertEqual(target_index[i], loaded_index[i])
        self.assertTrue(np.allclose(target_values, loaded_values))
        self.assertEqual(list(df.columns), list(loaded_df.columns))

        # test writing and reading Single Index dataframe to local files
        print(f'write and read a MultiIndex dataframe to all types of local files')
        df2 = set_primary_key_frame(self.df2, primary_key=['ts_code'], pk_dtypes=['str'])
        set_primary_key_index(df2, primary_key=['ts_code'], pk_dtypes=['str'])
        print(f'following dataframe with multiple index will be written to disk in all formats:\n'
              f'{df2}')
        self.ds_csv.write_file(df2, 'test_csv_file2')
        self.assertTrue(self.ds_csv.file_exists('test_csv_file2'))
        loaded_df = self.ds_csv.read_file('test_csv_file2',
                                          primary_key=['ts_code'],
                                          pk_dtypes=['str'])
        target_index = df2.index.values
        loaded_index = loaded_df.index.values
        target_values = np.array(df2.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved csv file is\n'
              f'{loaded_df}\n')
        for i in range(len(target_index)):
            self.assertEqual(target_index[i], loaded_index[i])
        rows, cols = target_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(target_values[i, j], loaded_values[i, j])
        self.assertEqual(list(df2.columns), list(loaded_df.columns))

        self.ds_hdf.write_file(df2, 'test_hdf_file2')
        self.assertTrue(self.ds_hdf.file_exists('test_hdf_file2'))
        loaded_df = self.ds_hdf.read_file('test_hdf_file2',
                                          primary_key=['ts_code'],
                                          pk_dtypes=['str'])
        target_index = df2.index.values
        loaded_index = loaded_df.index.values
        target_values = np.array(df2.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved hdf file is\n'
              f'{loaded_df}\n')
        for i in range(len(target_index)):
            self.assertEqual(target_index[i], loaded_index[i])
        rows, cols = target_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(target_values[i, j], loaded_values[i, j])
        self.assertEqual(list(df2.columns), list(loaded_df.columns))

        self.ds_fth.write_file(df2, 'test_fth_file2')
        self.assertTrue(self.ds_fth.file_exists('test_fth_file2'))
        loaded_df = self.ds_fth.read_file('test_fth_file2',
                                          primary_key=['ts_code'],
                                          pk_dtypes=['str'])
        target_index = df2.index.values
        loaded_index = loaded_df.index.values
        target_values = np.array(df2.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from saved feather file is\n'
              f'{loaded_df}\n')
        for i in range(len(target_index)):
            self.assertEqual(target_index[i], loaded_index[i])
        rows, cols = target_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(target_values[i, j], loaded_values[i, j])
        self.assertEqual(list(df2.columns), list(loaded_df.columns))

        print(f'Test getting file table coverages')
        cov = self.ds_csv.get_file_table_coverage('test_csv_file', 'ts_code',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=False)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ["000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ", "000005.SZ"])
        cov = self.ds_hdf.get_file_table_coverage('test_hdf_file', 'ts_code',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=False)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ["000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ", "000005.SZ"])
        cov = self.ds_fth.get_file_table_coverage('test_fth_file', 'ts_code',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=False)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ["000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ", "000005.SZ"])

        cov = self.ds_csv.get_file_table_coverage('test_csv_file', 'trade_date',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=False)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ['20211112', '20211113'])
        cov = self.ds_hdf.get_file_table_coverage('test_hdf_file', 'trade_date',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=False)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ['20211112', '20211113'])
        cov = self.ds_fth.get_file_table_coverage('test_fth_file', 'trade_date',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=False)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ['20211112', '20211113'])

        print(f'Test getting file table coverages with only min max and count')
        cov = self.ds_csv.get_file_table_coverage('test_csv_file', 'ts_code',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=True)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ["000001.SZ", "000005.SZ", 5])
        cov = self.ds_hdf.get_file_table_coverage('test_hdf_file', 'ts_code',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=True)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ["000001.SZ", "000005.SZ", 5])
        cov = self.ds_fth.get_file_table_coverage('test_fth_file', 'ts_code',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=True)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ["000001.SZ", "000005.SZ", 5])

        cov = self.ds_csv.get_file_table_coverage('test_csv_file', 'trade_date',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=True)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ['20211112', '20211113', 2])
        cov = self.ds_hdf.get_file_table_coverage('test_hdf_file', 'trade_date',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=True)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ['20211112', '20211113', 2])
        cov = self.ds_fth.get_file_table_coverage('test_fth_file', 'trade_date',
                                                  primary_key=['ts_code', 'trade_date'],
                                                  pk_dtypes=['str', 'TimeStamp'],
                                                  min_max_only=True)
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ['20211112', '20211113', 2])

        for ds in [self.ds_csv, self.ds_hdf, self.ds_fth]:
            # test reading dataframe from all datasources with selection
            print(f'Read a dataframe from datasource {ds} with selecting shares and start/end')
            df_res = set_primary_key_frame(self.built_in_df,
                                           primary_key=['ts_code', 'trade_date'],
                                           pk_dtypes=['varchar', 'date'])
            set_primary_key_index(df_res, primary_key=['ts_code', 'trade_date'], pk_dtypes=['varchar', 'date'])
            print(f'following dataframe with multiple index will be written to {ds}:\n'
                  f'{df_res}')
            ds.write_file(df_res, 'test_csv_file_chunk')
            self.assertTrue(ds.file_exists('test_csv_file_chunk'))
            shares = ['000001.SZ', '000003.SZ']
            start = '20211112'
            end = '20211113'
            loaded_df = ds.read_file(
                    'test_csv_file_chunk',
                    primary_key=['ts_code', 'trade_date'],
                    pk_dtypes=['varchar', 'date'],
                    share_like_pk='ts_code',
                    shares=shares,
                    date_like_pk='trade_date',
                    start=start,
                    end=end,
                    chunk_size=5
            )
            target_df = df_res.loc[df_res.index.isin(shares, level='ts_code')]
            m1 = target_df.index.get_level_values('trade_date') >= start
            m2 = target_df.index.get_level_values('trade_date') <= end
            target_df = target_df[m1 & m2]
            target_index = target_df.index.values
            loaded_index = loaded_df.index.values
            target_values = np.array(target_df.values)
            loaded_values = np.array(loaded_df.values)
            print(
                    f'df retrieved from {ds} selecting both shares {shares} and trade_dates {start}/'
                    f'{end}\n'
                    f'{loaded_df}\n')
            for i in range(len(target_index)):
                self.assertEqual(target_index[i], loaded_index[i])
            rows, cols = target_values.shape
            for i in range(rows):
                for j in range(cols):
                    self.assertEqual(target_values[i, j], loaded_values[i, j])
            self.assertEqual(list(df_res.columns), list(loaded_df.columns))

            # #################################################################
            print(f'Read a dataframe from {ds} with selecting shares {shares} and NO start/end')
            df_res = set_primary_key_frame(self.built_in_df,
                                           primary_key=['ts_code', 'trade_date'],
                                           pk_dtypes=['varchar', 'date'])
            set_primary_key_index(df_res, primary_key=['ts_code', 'trade_date'], pk_dtypes=['varchar', 'date'])
            print(f'following dataframe will be written to {ds} in all formats:\n'
                  f'{df_res}')
            ds.write_file(df_res, 'test_csv_file_chunk')
            self.assertTrue(ds.file_exists('test_csv_file_chunk'))
            shares = ['000001.SZ', '000003.SZ']
            start = '20211112'
            end = '20211113'
            loaded_df = ds.read_file(
                    file_name='test_csv_file_chunk',
                    primary_key=['ts_code', 'trade_date'],
                    pk_dtypes=['varchar', 'date'],
                    share_like_pk='ts_code',
                    shares=shares,
                    chunk_size=5
            )

            target_df = df_res.loc[df_res.index.isin(shares, level='ts_code')]
            target_index = target_df.index.values
            loaded_index = loaded_df.index.values
            target_values = np.array(target_df.values)
            loaded_values = np.array(loaded_df.values)
            print(f'df retrieved from {ds} selecting only shares {shares}\n'
                  f'{loaded_df}\n')
            for i in range(len(target_index)):
                self.assertEqual(target_index[i], loaded_index[i])
            rows, cols = target_values.shape
            for i in range(rows):
                for j in range(cols):
                    self.assertEqual(target_values[i, j], loaded_values[i, j])
            self.assertEqual(list(df_res.columns), list(loaded_df.columns))

            # #################################################################
            print(f'Read a dataframe from {ds} with selecting NO shares and ONLY start/end')
            df_res = set_primary_key_frame(self.built_in_df,
                                           primary_key=['ts_code', 'trade_date'],
                                           pk_dtypes=['varchar', 'date'])
            set_primary_key_index(df_res, primary_key=['ts_code', 'trade_date'], pk_dtypes=['varchar', 'date'])
            print(f'following dataframe will be written to {ds} in all formats:\n'
                  f'{df_res}')
            ds.write_file(df_res, 'test_csv_file_chunk')
            self.assertTrue(ds.file_exists('test_csv_file_chunk'))
            shares = ['000001.SZ', '000003.SZ']
            start = '20211112'
            end = '20211113'
            loaded_df = ds.read_file(
                    'test_csv_file_chunk',
                    primary_key=['ts_code', 'trade_date'],
                    pk_dtypes=['varchar', 'date'],
                    date_like_pk='trade_date',
                    start=start,
                    end=end,
                    chunk_size=5
            )

            target_df = df_res.copy()
            m1 = target_df.index.get_level_values('trade_date') >= start
            m2 = target_df.index.get_level_values('trade_date') <= end
            target_df = target_df[m1 & m2]
            target_index = target_df.index.values
            loaded_index = loaded_df.index.values
            target_values = np.array(target_df.values)
            loaded_values = np.array(loaded_df.values)
            print(f'df retrieved from {ds} selecting ONLY trade_dates: {start}/{end}\n'
                  f'{loaded_df}\n')
            for i in range(len(target_index)):
                self.assertEqual(target_index[i], loaded_index[i])
            rows, cols = target_values.shape
            for i in range(rows):
                for j in range(cols):
                    self.assertEqual(target_values[i, j], loaded_values[i, j])
            self.assertEqual(list(df_res.columns), list(loaded_df.columns))

    def test_write_and_read_database(self):
        """ test DataSource method read_database and write_database"""
        print(f'write and read a MultiIndex dataframe to database')
        df = set_primary_key_frame(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'TimeStamp'])
        print(f'following dataframe with multiple index will be written to local database:\n'
              f'{df}')

        con = connect(
                host=self.ds_db.host,
                port=self.ds_db.port,
                user=self.ds_db.__user__,
                password=self.ds_db.__password__,
                db=self.ds_db.db_name,
        )
        cursor = con.cursor()
        table_name = 'test_db_table'
        # 删除数据库中的临时表
        sql = f"DROP TABLE IF EXISTS {table_name}"
        cursor.execute(sql)
        con.commit()
        con.close()
        # 为确保update顺利进行，建立新表并设置primary_key
        self.ds_db.write_database(df, table_name)
        loaded_df = self.ds_db.read_database(table_name)
        saved_index = df.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        print(f'retrieve whole arr table from database\n'
              f'df retrieved from database is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(self.df.columns), list(loaded_df.columns))
        # test reading partial of the datatable
        loaded_df = self.ds_db.read_database(table_name,
                                             share_like_pk='ts_code',
                                             shares=["000001.SZ", "000003.SZ"],
                                             date_like_pk='trade_date',
                                             start='20211112',
                                             end='20211112')
        print(f'retrieve partial arr table from database with:\n'
              f'shares = ["000001.SZ", "000003.SZ"]\n'
              f'start/end = 20211112/20211112\n'
              f'df retrieved from database is\n'
              f'{loaded_df}\n')
        saved_index = df.index.values
        saved_values = np.array(df.values)
        loaded_values = np.array(loaded_df.values)
        # 逐一判断读取出来的df的每一行是否正确
        row, col = saved_values.shape
        for j in range(col):
            self.assertEqual(saved_values[0, j], loaded_values[0, j])
            self.assertEqual(saved_values[2, j], loaded_values[1, j])
        self.assertEqual(list(self.df.columns), list(loaded_df.columns))

        print(f'write and read a MultiIndex dataframe to database')
        print(f'following dataframe with multiple index will be written to database:\n'
              f'{self.df2}')
        con = connect(
                host=self.ds_db.host,
                port=self.ds_db.port,
                user=self.ds_db.__user__,
                password=self.ds_db.__password__,
                db=self.ds_db.db_name,
        )
        cursor = con.cursor()
        table_name = 'test_db_table2'
        # 删除数据库中的临时表
        sql = f"DROP TABLE IF EXISTS {table_name}"
        cursor.execute(sql)
        con.commit()
        con.close()

        self.ds_db.write_database(self.df2, table_name)
        loaded_df = self.ds_db.read_database(table_name)
        saved_index = self.df2.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(self.df2.values)
        loaded_values = np.array(loaded_df.values)
        print(f'df retrieved from database is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(self.df2.columns), list(loaded_df.columns))
        # test reading partial of the datatable
        loaded_df = self.ds_db.read_database(table_name,
                                             share_like_pk='ts_code',
                                             shares=["000001.SZ", "000003.SZ", "000004.SZ", "000009.SZ", "000005.SZ"])
        print(f'retrieve partial arr table from database with:\n'
              f'shares = ["000001.SZ", "000003.SZ", "000004.SZ", "000009.SZ", "000005.SZ"]\n'
              f'df retrieved from saved csv file is\n'
              f'{loaded_df}\n')
        saved_values = np.array(self.df2.values)
        loaded_values = np.array(loaded_df.values)
        # 逐一判断读取出来的df的每一行是否正确
        row, col = saved_values.shape
        for j in range(col):
            self.assertEqual(saved_values[0, j], loaded_values[0, j])
            self.assertEqual(saved_values[2, j], loaded_values[1, j])
            self.assertEqual(saved_values[3, j], loaded_values[2, j])
            self.assertEqual(saved_values[4, j], loaded_values[3, j])
            self.assertEqual(saved_values[8, j], loaded_values[4, j])
        self.assertEqual(list(self.df2.columns), list(loaded_df.columns))

        print(f'Test getting database table coverages')
        cov = self.ds_db.get_db_table_coverage(table_name, 'ts_code')
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ["000001.SZ", "000002.SZ", "000003.SZ", "000004.SZ", "000005.SZ",
                          "000006.SZ", "000007.SZ", "000008.SZ", "000009.SZ", "000010.SZ"])

        cov = self.ds_db.get_db_table_coverage('test_db_table', 'trade_date')
        print(cov)
        self.assertIsInstance(cov, list)
        self.assertEqual(cov,
                         ['20211112', '20211113'])

    def test_update_database(self):
        """ test the function update_database()"""
        print(f'update a database table with new arr on same primary key')
        df = set_primary_key_frame(self.df, primary_key=['ts_code', 'trade_date'], pk_dtypes=['str', 'TimeStamp'])
        df_add = set_primary_key_frame(self.df_add, primary_key=['ts_code', 'trade_date'],
                                       pk_dtypes=['str', 'TimeStamp'])
        df_res = set_primary_key_frame(self.df_res, primary_key=['ts_code', 'trade_date'],
                                       pk_dtypes=['str', 'TimeStamp'])
        print(f'following dataframe with be written to an empty data-table:\n'
              f'{df}\n'
              f'and following dataframe will be used to updated that database table\n'
              f'{df_add}')
        table_name = 'test_db_table'
        # 删除数据库中的临时表
        self.ds_db.drop_table_data(table_name)
        # 为确保update顺利进行，建立新表并设置primary_key
        self.ds_db.new_db_table(table_name,
                                columns=['ts_code', 'trade_date', 'open', 'high', 'low', 'close'],
                                dtypes=['varchar(9)', 'date', 'float', 'float', 'float', 'float'],
                                primary_key=['ts_code', 'trade_date'])
        self.ds_db.write_database(df, table_name)
        self.ds_db.update_database(df_add, table_name, ['ts_code', 'trade_date'])
        loaded_df = self.ds_db.read_database(table_name)
        saved_index = df_res.index.values
        loaded_index = loaded_df.index.values
        saved_values = np.array(df_res.values)
        loaded_values = np.array(loaded_df.values)
        print(f'retrieve whole arr table from database\n'
              f'df retrieved from database is\n'
              f'{loaded_df}\n')
        for i in range(len(saved_index)):
            self.assertEqual(saved_index[i], loaded_index[i])
        rows, cols = saved_values.shape
        for i in range(rows):
            for j in range(cols):
                if pd.isna(saved_values[i, j]):
                    self.assertTrue(pd.isna(loaded_values[i, j]))
                else:
                    self.assertEqual(saved_values[i, j], loaded_values[i, j])
        self.assertEqual(list(self.df.columns), list(loaded_df.columns))

    # noinspection PyPep8Naming
    def test_read_write_update_table_data(self):
        """ test DataSource method read_table_data() and write_table_data()
            will test both built-in tables and user-defined tables
        """
        # 测试前删除已经存在的数据表
        test_table = 'stock_daily'
        all_data_sources = [self.ds_csv, self.ds_hdf, self.ds_fth, self.ds_db]
        for data_source in all_data_sources:
            data_source.drop_table_data(test_table)
        # 测试写入标准表数据
        for data_source in all_data_sources:
            data_source.write_table_data(self.built_in_df, test_table)

        # 测试完整读出标准表数据
        for data_source in all_data_sources:
            df = data_source.read_table_data(test_table)
            print(f'df read from arr source: \n{data_source.source_type}-{data_source.connection_type} \nis:\n{df}')
            ts_codes = ['000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                        '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ',
                        '000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ']
            trade_dates = pd.to_datetime(
                    ['20211112', '20211112', '20211112', '20211112', '20211112',
                     '20211113', '20211113', '20211113', '20211113', '20211113',
                     '20211114', '20211114', '20211114', '20211114', '20211114']
            )
            cols = ['open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount']
            for tc, td in zip(ts_codes, trade_dates):
                df_val = df.loc[(tc, td)].values
                tdf = self.built_in_df
                t_val = tdf.loc[(tdf.ts_code == tc) & (tdf.trade_date == td)][cols].values
                print(f'on row: {tc}, {td}\n'
                      f'arr read from local source: {df_val}\n'
                      f'arr from origin dataframe : {t_val}')
                self.assertTrue(np.allclose(df_val, t_val))

        # 测试读出并筛选部分标准表数据
        for data_source in all_data_sources:
            df = data_source.read_table_data(test_table,
                                             shares=['000001.SZ', '000002.SZ', '000005.SZ', '000007.SZ'],
                                             start='20211113',
                                             end='20211116')
            print(f'df read from arr source: \n{data_source.source_type}-{data_source.connection_type} \nis:\n{df}')

        # 测试update table数据到本地文件或数据，合并类型为"ignore"
        for data_source in all_data_sources:
            df = data_source.fetch_history_table_data(test_table, 'df', df=self.built_in_add_df)
            data_source.update_table_data(test_table, df, 'ignore')
            df = data_source.read_table_data(test_table)
            print(f'df read from arr source after updating with merge type IGNORE:\n'
                  f'{data_source.source_type}-{data_source.connection_type}\n{df}')

        # 测试update table数据到本地文件或数据，合并类型为"update"
        # 测试前删除已经存在的（真实）数据表
        test_table = 'stock_daily'
        all_data_sources = [self.ds_csv, self.ds_hdf, self.ds_fth, self.ds_db]
        for data_source in all_data_sources:
            data_source.drop_table_data(test_table)
        # 测试写入标准表数据
        for data_source in all_data_sources:
            data_source.write_table_data(self.built_in_df, test_table)
        # 测试写入新增数据并设置合并类型为"update"
        for data_source in all_data_sources:
            df = data_source.fetch_history_table_data(test_table, 'df', df=self.built_in_add_df)
            data_source.update_table_data(test_table, df, 'update')
            df = data_source.read_table_data(test_table)
            print(f'df read from arr source after updating with merge type UPDATE:\n'
                  f'{data_source.source_type}-{data_source.connection_type}\n{df}')

        # 测试读出并筛选部分标准表数据
        for data_source in all_data_sources:
            df = data_source.read_table_data(test_table,
                                             shares=['000001.SZ', '000002.SZ', '000005.SZ', '000007.SZ'],
                                             start='20211113',
                                             end='20211116')
            print(f'df read from arr source: \n{data_source.source_type}-{data_source.connection_type} \nis:\n{df}')

        self.assertEqual(self.ds_csv.tables, ['stock_daily'])
        self.assertEqual(self.ds_hdf.tables, ['stock_daily'])
        self.assertEqual(self.ds_fth.tables, ['stock_daily'])
        self.assertEqual(self.ds_db.tables, ['stock_daily'])

    def test_export_table_data(self):
        """ 测试函数datasource.export_table_data"""
        # TODO: implement this test
        pass

    def test_download_update_table_data(self):
        """ test downloading arr from tushare"""
        tables_to_test = {'stock_daily':     {'ts_code':    None,
                                              'trade_date': '20211112'},
                          'stock_weekly':    {'ts_code':    None,
                                              'trade_date': '20211008'},
                          'stock_indicator': {'ts_code':    None,
                                              'trade_date': '20211112'},
                          'trade_calendar':  {'exchange': 'SSE',
                                              'start':    '19910701',
                                              'end':      '19920701'}
                          }
        tables_to_add = {'stock_daily':     {'ts_code':    None,
                                             'trade_date': '20211115'},
                         'stock_weekly':    {'ts_code':    None,
                                             'trade_date': '20211015'},
                         'stock_indicator': {'ts_code':    None,
                                             'trade_date': '20211115'},
                         'trade_calendar':  {'exchange': 'SZSE',
                                             'start':    '19910701',
                                             'end':      '19920701'}
                         }
        all_data_sources = [self.ds_csv, self.ds_hdf, self.ds_fth, self.ds_db]

        for table in tables_to_test:
            # 删除已有的表
            for ds in all_data_sources:
                ds.drop_table_data(table)
            # 下载并写入数据到表中
            print(f'downloading table arr ({table}) with parameter: \n'
                  f'{tables_to_test[table]}')
            df = self.ds_csv.fetch_history_table_data(table, 'tushare', **tables_to_test[table])
            print(f'---------- Done! got:---------------\n{df}\n--------------------------------')
            for ds in all_data_sources:
                print(f'updating IGNORE table arr ({table}) from tushare for '
                      f'datasource: {ds.source_type}-{ds.connection_type}')
                ds.update_table_data(table, df, 'ignore')
                print(f'-- Done! --')
                ds.overview()

            for ds in all_data_sources:
                print(f'reading table arr ({table}) from tushare for '
                      f'datasource: {ds.source_type}-{ds.connection_type}')
                if table != 'trade_calendar':
                    df = ds.read_table_data(table, shares=['000001.SZ', '000002.SZ', '000007.SZ', '600067.SH'])
                else:
                    df = ds.read_table_data(table, start='20200101', end='20200301')
                print(f'got arr from arr source {ds.source_type}-{ds.connection_type}:\n{df}')
                ds.overview()

            # 下载数据并添加到表中
            print(f'downloading table arr ({table}) with parameter: \n'
                  f'{tables_to_add[table]}')
            df = self.ds_hdf.fetch_history_table_data(table, 'tushare', **tables_to_add[table])
            print(f'---------- Done! got:---------------\n{df}\n--------------------------------')
            for ds in all_data_sources:
                print(f'updating UPDATE table arr ({table}) from tushare for '
                      f'datasource: {ds.source_type}-{ds.connection_type}')
                ds.update_table_data(table, df, 'update')
                print(f'-- Done! --')
                ds.overview()

            for ds in all_data_sources:
                print(f'reading table arr ({table}) from tushare for '
                      f'datasource: {ds.source_type}-{ds.connection_type}')
                if table != 'trade_calendar':
                    df = ds.read_table_data(table, shares=['000004.SZ', '000005.SZ', '000006.SZ'])
                else:
                    df = ds.read_table_data(table, start='20200101', end='20200201')
                print(f'got arr from arr source {ds.source_type}-{ds.connection_type}:\n{df}')
                ds.overview()

            # 删除所有的表
            for ds in all_data_sources:
                ds.drop_table_data(table)
                print('all table data are cleared')
                ds.overview()

    def test_get_history_panel_data(self):
        """ test getting arr, from real database """
        ds = qt.QT_DATA_SOURCE
        shares = ['000001.SZ', '000002.SZ', '600067.SH', '000300.SH', '518860.SH']
        htypes = 'pe, close, open, swing, strength'
        htypes = str_to_list(htypes)
        start = '20210101'
        end = '20210301'
        asset_type = 'E, IDX, FD'
        freq = 'd'
        adj = 'back'
        dfs = ds.get_history_data(shares=shares,
                                  htypes=htypes,
                                  start=start,
                                  end=end,
                                  asset_type=asset_type,
                                  freq=freq,
                                  adj=adj)
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htypes)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))
        print(f'got history panel with backward price recover:\n{dfs}')
        dfs = ds.get_history_data(shares=shares,
                                  htypes=htypes,
                                  start=start,
                                  end=end,
                                  asset_type=asset_type,
                                  freq=freq,
                                  adj='forward')
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htypes)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))
        print(f'got history panel with forward price recover:\n{dfs}')
        dfs = ds.get_history_data(shares=shares,
                                  htypes=htypes,
                                  start=start,
                                  end=end,
                                  asset_type=asset_type,
                                  freq=freq,
                                  adj='forward')
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htypes)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))
        print(f'got history panel with price:\n{dfs}')
        htypes = ['open', 'high', 'low', 'close', 'vol', 'manager_name']
        dfs = ds.get_history_data(shares=shares,
                                  htypes=htypes,
                                  start=start,
                                  end=end,
                                  asset_type=asset_type,
                                  freq='w',
                                  adj='forward')
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), htypes)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))
        print(f'got history data:\n{dfs}')
        dfs = ds.get_history_data(shares=shares,
                                  htypes='close, high',
                                  start=None,
                                  end=None,
                                  row_count=20,
                                  asset_type='E, IDX, FD',
                                  freq='d',
                                  adj='none')
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), ['close', 'high'])
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))
        print(f'got history data:\n{dfs}')

    def test_get_index_weights(self):
        """ test get_index_weights() function"""
        ds = qt.QT_DATA_SOURCE
        dfs = ds.get_index_weights('000300.SH,000002.SZ',
                                   start='20200101',
                                   end='20200102',
                                   shares='000001.SZ, 000002.SZ, 000003.SZ,601728.SH')
        self.assertIsInstance(dfs, dict)
        self.assertEqual(list(dfs.keys()), ['wt-000300.SH', 'wt-000002.SZ'])
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in dfs.values()))
        print(dfs)

    def test_get_table_info(self):
        """ 获取打印数据表的基本信息"""
        ds = qt.QT_DATA_SOURCE
        ds.get_table_info('trade_calendar')
        ds.get_table_info('stock_basic')
        ds.get_table_info('stock_5min')
        ds.get_table_info('stock_1min')
        ds.get_table_info('future_daily')
        ds.get_table_info('fund_hourly')
        ds.get_table_info('fund_nav')

    def test_table_overview(self):
        """ 所有数据表的基本信息打印"""
        qt_ds = qt.QT_DATA_SOURCE
        df_trade_calendar = qt_ds.read_table_data('trade_calendar',
                                                  start='20200101',
                                                  end='20200201')
        df_stock_basic = qt_ds.read_table_data('stock_basic',
                                               shares=['000001.SZ', '000002.SZ'],
                                               start='20200101', end='20200201')
        for ds in [self.ds_csv, self.ds_db, self.ds_hdf, self.ds_db]:
            print(f'-- {ds.source_type}-{ds.connection_type} --')
            print('write data to datasource')
            ds.update_table_data('trade_calendar', df_trade_calendar)
            ds.update_table_data('stock_basic', df_stock_basic)

            ov = ds.overview()
            print(ov[['has_data', 'size', 'records']])
            print(ov[['pk1', 'min1', 'max1']])
            print(ov[['pk2', 'min2', 'max2']])

    def test_get_related_tables(self):
        """根据数据名称查找相关数据表及数据列名称"""
        # 精确查找数据表及数据列
        tbls = htype_to_table_col(htypes='close', freq='d')
        print("by: htype_to_table_col(htypes='close', freq='d')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'stock_daily': ['close']}
        )
        tbls = htype_to_table_col(htypes='invest_income', freq='q', asset_type='E')
        print("by: htype_to_table_col(htypes='invest_income', freq='q', asset_type='E')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'income': ['invest_income']}
        )
        # 精确查找多个数据表及数据列
        tbls = htype_to_table_col(htypes='close, open', freq='d', asset_type='E', method='exact')
        print("by: htype_to_table_col(htypes='close, open', freq='d', asset_type='E', method='exact')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'stock_daily': ['close', 'open']}
        )
        tbls = htype_to_table_col(htypes='close, open', freq='d, w', asset_type='E, IDX', method='exact')
        print("by: htype_to_table_col(htypes='close, open', freq='d, w', asset_type='E, IDX', method='exact')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'index_weekly': ['open'],
                 'stock_daily':  ['close']}
        )
        tbls = htype_to_table_col(htypes='close, manager_name', freq='d', asset_type='E')
        print("by: htype_to_table_col(htypes='close, manager_name', freq='d', asset_type='E')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'stk_managers': ['name'],
                 'stock_daily':  ['close']}
        )
        tbls = htype_to_table_col(htypes='close, open', freq='d, w', asset_type='E, IDX')
        print("by: htype_to_table_col(htypes='close, open', freq='d, w', asset_type='E, IDX')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'index_daily':  ['close', 'open'],
                 'index_weekly': ['close', 'open'],
                 'stock_daily':  ['close', 'open'],
                 'stock_weekly': ['close', 'open']}
        )
        # 部分无法精确匹配时，只输出可以匹配的部分
        tbls = htype_to_table_col(htypes='close, opan', freq='d, w', asset_type='E, IDX')
        print("by: htype_to_table_col(htypes='close, opan', freq='d, w', asset_type='E, IDX')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'index_daily':  ['close'],
                 'index_weekly': ['close'],
                 'stock_daily':  ['close'],
                 'stock_weekly': ['close']}
        )
        tbls = htype_to_table_col(htypes='close, opan', freq='d, t', asset_type='E, IDX', method='exact')
        print("by: htype_to_table_col(htypes='close, opan', freq='d, t', asset_type='E, IDX', method='exact')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'stock_daily': ['close']}
        )
        # 全部无法精确匹配时，不报错，输出空集合
        tbls = htype_to_table_col(htypes='clese, opan', freq='d, t', asset_type='E, IDX', method='exact')
        print("by: htype_to_table_col(htypes='close, opan', freq='d, t', asset_type='E, IDX', method='exact')")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {}
        )
        # 当soft_freq为True时，匹配查找相应的可等分freq
        tbls = htype_to_table_col(htypes='close, open', freq='2d',
                                  asset_type='E, IDX', method='exact', soft_freq=True)
        print(f"by: htype_to_table_col(htypes='close, open', freq='2d, 2d', "
              f"asset_type='E, IDX', method='exact', soft_freq=True)")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'stock_daily': ['close'],
                 'index_daily': ['open']}
        )

        tbls = htype_to_table_col(htypes='close, pe, invest_income', freq='w-Sun, 45min',
                                  asset_type='E, IDX', method='permute', soft_freq=True)
        print(f"by: htype_to_table_col(htypes='close, pe, invest_income', freq='w-Sun, 45min', "
              f"asset_type='E, IDX', method='permute', soft_freq=True)")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'stock_weekly':    ['close'],
                 'index_weekly':    ['close'],
                 'stock_15min':     ['close'],
                 'index_15min':     ['close'],
                 'stock_indicator': ['pe'],
                 'index_indicator': ['pe'],
                 'income':          ['invest_income']
                 }
        )

        tbls = htype_to_table_col(htypes='close, pe, invest_income', freq='w-Sun',
                                  asset_type='E, IDX', method='exact', soft_freq=True)
        print(f"by: htype_to_table_col(htypes='close, pe, invest_income', freq='w-Sun, 45min', "
              f"asset_type='E, IDX', method='exact', soft_freq=True)")
        print(f'found table: {tbls}')
        self.assertEqual(
                tbls,
                {'stock_weekly':    ['close'],
                 'index_indicator': ['pe'],
                 'income':          ['invest_income']
                 }
        )

    def test_freq_resample(self):
        """ 测试freq_up与freq_down两个函数，确认是否能按股市交易规则正确转换数据频率（频率到日频以下时，仅保留交易时段）"""
        print(f'build test data')
        weekly_index = pd.date_range(start='20200101', end='20200331', freq='W-Fri')
        hourly_index = pd.date_range(start='20200101', end='20200110', freq='H')
        hourly_index_tt = hourly_index[hourly_index.indexer_between_time('9:00:00', '15:00:00')]

        test_data1 = np.random.randint(20, size=(13, 7)).astype('float')  # 用于daily_index数据
        test_data2 = np.random.randint(10, size=(217, 11)).astype('float')  # 用于sub_daily_index数据

        columns1 = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        columns2 = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']

        weekly_data = pd.DataFrame(test_data1, index=weekly_index, columns=columns1)
        hourly_data = pd.DataFrame(test_data2, index=hourly_index, columns=columns2)
        hourly_data_tt = hourly_data.reindex(index=hourly_index_tt)

        print(f'test resample, above daily freq')
        print(f'hourly data:\n{hourly_data.head(25)}')
        print(f'hourly data tt:\n{hourly_data_tt.head(25)}')
        print(f'verify that resampled from hourly data and hourly tt data are the same')
        resampled = _resample_data(hourly_data, target_freq='15min', method='ffill', b_days_only=False)
        resampled_tt = _resample_data(hourly_data_tt, target_freq='15min', method='ffill', b_days_only=False)
        self.assertTrue(np.allclose(resampled, resampled_tt))
        print('checks resample hourly data to 15 min')
        print(f'resampled data:\n{resampled.head(25)}')
        print(f'houly data:\n{hourly_data_tt.head(15)}')
        sampled_rows = [(0, 2), (2, 6), (6, 9), (None, None), (9, 12), (12, 16), (16, 16)]
        for day in range(9):
            for pos in range(len(sampled_rows)):
                start = sampled_rows[pos][0]
                end = sampled_rows[pos][1]
                if start is None:
                    continue
                for row in range(start + day * 17, end + day * 17):
                    res = hourly_data_tt.iloc[pos + day * 7].values
                    target = resampled.iloc[row].values
                    self.assertTrue(np.allclose(res, target))

        print('checks resample hourly data to 2d')
        resampled_1 = _resample_data(hourly_data, target_freq='2d', method='ffill')
        resampled_2 = _resample_data(hourly_data, target_freq='2d', method='bfill')
        resampled_3 = _resample_data(hourly_data, target_freq='2d', method='nan')
        resampled_4 = _resample_data(hourly_data, target_freq='2d', method='zero')
        print(resampled_1)
        print(resampled_2)
        print(resampled_3)
        print(resampled_4)
        print('resample with improper methods and check if they are same as "first"')
        self.assertTrue(np.allclose(resampled_1, resampled_2))
        self.assertTrue(np.allclose(resampled_1, resampled_3))
        self.assertTrue(np.allclose(resampled_1, resampled_4))

        print('check sample hourly data to d with proper methods, with none business days')
        resampled_1 = _resample_data(hourly_data, target_freq='d', method='last', b_days_only=False)
        resampled_2 = _resample_data(hourly_data, target_freq='d', method='mean', b_days_only=False)
        print(resampled_1)
        sampled_rows = [23, 47, 71, 95, 119, 143, 167, 191, 215]
        for pos in range(len(sampled_rows)):
            res = resampled_1.iloc[pos].values
            target = hourly_data.iloc[sampled_rows[pos]].values
            print(f'resampled row is \n{res}\n'
                  f'target row is \n{target}')
            self.assertTrue(np.allclose(res, target))

        print(resampled_2)
        sampled_row_starts = [0, 24, 48, 72, 96, 120, 144, 168, 192]
        sampled_row_ends = [24, 48, 72, 96, 120, 144, 168, 192, 216]
        for pos in range(len(sampled_rows)):
            res = resampled_2.iloc[pos].values
            start = sampled_row_starts[pos]
            end = sampled_row_ends[pos]
            target = hourly_data.iloc[start:end].values.mean(0)
            self.assertTrue(np.allclose(res, target))

        print('check sample hourly data to d with proper methods, without none business days')
        resampled_1 = _resample_data(hourly_data, target_freq='d', method='last')
        resampled_2 = _resample_data(hourly_data, target_freq='d', method='mean')
        print(resampled_1)
        print(hourly_data.to_string())
        # 被选出的交易日：
        selected_days = [1, 2, 5, 6, 7, 8, 9]
        # 计算被选出个交易日最后一个小时的序号
        sampled_rows = [min(d * 24 + 23, len(hourly_data) - 1) for d in selected_days]
        for pos in range(len(sampled_rows)):
            res = resampled_1.iloc[pos].values
            target = hourly_data.iloc[sampled_rows[pos]].values
            print(f'resampled row ({pos}) is \n{res}\n'
                  f'hourly data last row ({sampled_rows[pos]}) is \n{target}')
            self.assertTrue(np.allclose(res, target))

        print(resampled_2)
        # 计算被选出个交易日第一个小时和下一天第一个小时的序号
        sampled_row_starts = [d * 24 for d in selected_days]
        sampled_row_ends = [min(d * 24 + 24, len(hourly_data)) for d in selected_days]
        for pos in range(len(sampled_rows)):
            res = resampled_2.iloc[pos].values
            start = sampled_row_starts[pos]
            end = sampled_row_ends[pos]
            target = hourly_data.iloc[start:end].values.mean(0)
            print(f'resampled row ({pos}) is \n{res}\n'
                  f'hourly-data [{start}:{end}] averaged is \n{target}')
            self.assertTrue(np.allclose(res, target))

        print('resample daily data to 30min data')
        daily_data = _resample_data(hourly_data, target_freq='d', method='last', b_days_only=False).iloc[0:4]
        print(daily_data)
        resampled = _resample_data(daily_data, target_freq='30min', method='ffill', b_days_only=False)
        print(resampled)
        # TODO: last day data missing when resampling daily data to sub-daily data
        #   this is to be improved
        sampled_rows = [(0, 9), (9, 18), (18, 27)]
        for pos in range(len(sampled_rows)):
            for row in range(sampled_rows[pos][0], sampled_rows[pos][1]):
                res = daily_data.iloc[pos].values
                target = resampled.iloc[row].values
                self.assertTrue(np.allclose(res, target))

        print(f'test resample, below daily freq')
        print(weekly_data)
        print('resample weekly data to daily ffill')
        resampled = _resample_data(weekly_data, target_freq='d', method='ffill', b_days_only=False)
        print(resampled)
        sampled_rows = [(0, 7), (7, 14), (14, 21), (21, 28), (28, 35), (35, 42),
                        (42, 49), (49, 56), (56, 63), (63, 70), (70, 77), (77, 84)]
        for pos in range(len(sampled_rows)):
            for row in range(sampled_rows[pos][0], sampled_rows[pos][1]):
                res = weekly_data.iloc[pos].values
                target = resampled.iloc[row].values
                self.assertTrue(np.allclose(res, target))

        print('resample weekly data to daily bfill')
        resampled = _resample_data(weekly_data, target_freq='d', method='bfill', b_days_only=False)
        print(resampled)
        sampled_rows = [(0, 1), (1, 8), (8, 15), (15, 22), (22, 29), (29, 36),
                        (36, 43), (43, 50), (50, 57), (57, 64), (64, 71), (71, 78), (78, 84)]
        for pos in range(len(sampled_rows)):
            for row in range(sampled_rows[pos][0], sampled_rows[pos][1]):
                res = weekly_data.iloc[pos].values
                target = resampled.iloc[row].values
                self.assertTrue(np.allclose(res, target))

        print('resample weekly data to daily none')
        resampled = _resample_data(weekly_data, target_freq='d', method='nan', b_days_only=False)
        print(resampled)
        sampled_rows = [0, 7, 14, 21, 28, 35, 42, 49, 56, 63, 70, 77, 84]
        for pos in range(len(resampled)):
            res = resampled.iloc[pos].values
            if pos in sampled_rows:
                row = sampled_rows.index(pos)
                target = weekly_data.iloc[row].values
                self.assertTrue(np.allclose(res, target))
            else:
                self.assertTrue(all(np.isnan(item) for item in res))

        print('resample weekly data to daily zero')
        resampled = _resample_data(weekly_data, target_freq='d', method='zero', b_days_only=False)
        print(resampled)
        sampled_rows = [0, 7, 14, 21, 28, 35, 42, 49, 56, 63, 70, 77, 84]
        for pos in range(len(resampled)):
            res = resampled.iloc[pos].values
            if pos in sampled_rows:
                row = sampled_rows.index(pos)
                target = weekly_data.iloc[row].values
                self.assertTrue(np.allclose(res, target))
            else:
                self.assertTrue(all(item == 0. for item in res))

        print('resample weekly data to bi-weekly sunday last with none business days')
        resampled = _resample_data(weekly_data, target_freq='2w-Sun', method='last', b_days_only=False)
        print(resampled)
        sampled_rows = [0, 2, 4, 6, 8, 10]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[sampled_rows[pos]].values
            self.assertTrue(np.allclose(res, target))

        print('resample weekly data to bi-weekly sunday last without none business days')
        resampled = _resample_data(weekly_data, target_freq='2w-Sun', method='last', b_days_only=False)
        print(resampled)
        sampled_rows = [0, 2, 4, 6, 8, 10]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[sampled_rows[pos]].values
            self.assertTrue(np.allclose(res, target))

        print('resample weekly data to biweekly Friday last')
        resampled = _resample_data(weekly_data, target_freq='2w-Fri', method='last', b_days_only=False)
        print(resampled)
        sampled_rows = [0, 2, 4, 6, 8, 10, 12]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[sampled_rows[pos]].values
            self.assertTrue(np.allclose(res, target))

        print('resample weekly data to biweekly Friday last without none business days')
        resampled = _resample_data(weekly_data, target_freq='2w-Fri', method='last', b_days_only=False)
        print(resampled)
        sampled_rows = [0, 2, 4, 6, 8, 10, 12]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[sampled_rows[pos]].values
            self.assertTrue(np.allclose(res, target))

        print('resample weekly data to biweekly Wednesday first')
        resampled = _resample_data(weekly_data, target_freq='2w-Wed', method='first', b_days_only=False)
        print(resampled)
        sampled_rows = [0, 1, 3, 5, 7, 9]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[sampled_rows[pos]].values
            self.assertTrue(np.allclose(res, target))

        print('resample weekly data to monthly sum')
        resampled = _resample_data(weekly_data, target_freq='m', method='sum', b_days_only=False)
        print(resampled)
        sampled_rows = [(0, 1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12)]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[np.array(sampled_rows[pos])].values.sum(0)
            self.assertTrue(np.allclose(res, target))

        print('resample weekly data to monthly sum without none business days')
        resampled = _resample_data(weekly_data, target_freq='m', method='sum', b_days_only=False)
        print(resampled)
        sampled_rows = [(0, 1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12)]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[np.array(sampled_rows[pos])].values.sum(0)
            self.assertTrue(np.allclose(res, target))

        print('resample weekly data to monthly max')
        resampled = _resample_data(weekly_data, target_freq='m', method='high', b_days_only=False)
        print(resampled)
        sampled_rows = [(0, 1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12)]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[np.array(sampled_rows[pos])].values.max(0)
            self.assertTrue(np.allclose(res, target))

        print('resample weekly data to monthly avg')
        resampled = _resample_data(weekly_data, target_freq='m', method='mean', b_days_only=False)
        print(resampled)
        sampled_rows = [(0, 1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11, 12)]
        for pos in range(len(sampled_rows)):
            res = resampled.iloc[pos].values
            target = weekly_data.iloc[np.array(sampled_rows[pos])].values.mean(0)
            self.assertTrue(np.allclose(res, target))

    def test_trade_time_index(self):
        """ 测试函数是否能正确生成交易时段的indexer"""
        print('create datetime index with freq "D" and keep non-trading days')
        indexer = _trade_time_index('20200101', '20200105', freq='d', trade_days_only=False)
        print(f'the output is {indexer}')
        self.assertIsInstance(indexer, pd.DatetimeIndex)
        self.assertEqual(len(indexer), 5)
        self.assertEqual(list(indexer), [pd.to_datetime('20200101'),
                                         pd.to_datetime('20200102'),
                                         pd.to_datetime('20200103'),
                                         pd.to_datetime('20200104'),
                                         pd.to_datetime('20200105')])

        print('create datetime index with freq "D" without non-trading days')
        indexer = _trade_time_index('20200101', '20200105', freq='d')
        print(f'the output is {indexer}')
        self.assertIsInstance(indexer, pd.DatetimeIndex)
        self.assertEqual(len(indexer), 2)
        self.assertEqual(list(indexer), [pd.to_datetime('20200102'),
                                         pd.to_datetime('20200103')])

        print('create datetime index with freq "30min" with default trade time with non_trading days')
        indexer = _trade_time_index('20200101', '20200103', freq='30min', trade_days_only=False)
        print(f'the output is {indexer}')
        self.assertIsInstance(indexer, pd.DatetimeIndex)
        self.assertEqual(len(indexer), 18)
        self.assertEqual(list(indexer),
                         list(pd.to_datetime(['2020-01-01 09:30:00', '2020-01-01 10:00:00',
                                              '2020-01-01 10:30:00', '2020-01-01 11:00:00',
                                              '2020-01-01 11:30:00', '2020-01-01 13:30:00',
                                              '2020-01-01 14:00:00', '2020-01-01 14:30:00',
                                              '2020-01-01 15:00:00', '2020-01-02 09:30:00',
                                              '2020-01-02 10:00:00', '2020-01-02 10:30:00',
                                              '2020-01-02 11:00:00', '2020-01-02 11:30:00',
                                              '2020-01-02 13:30:00', '2020-01-02 14:00:00',
                                              '2020-01-02 14:30:00', '2020-01-02 15:00:00'])
                              )
                         )

        print('create datetime index with freq "30min" with default trade time without non_trading days')
        indexer = _trade_time_index('20200101', '20200103', freq='30min', trade_days_only=True)
        print(f'the output is {indexer}')
        self.assertIsInstance(indexer, pd.DatetimeIndex)
        self.assertEqual(len(indexer), 9)
        self.assertEqual(list(indexer),
                         list(pd.to_datetime(['2020-01-02 09:30:00', '2020-01-02 10:00:00',
                                              '2020-01-02 10:30:00', '2020-01-02 11:00:00',
                                              '2020-01-02 11:30:00', '2020-01-02 13:30:00',
                                              '2020-01-02 14:00:00', '2020-01-02 14:30:00',
                                              '2020-01-02 15:00:00'])
                              )
                         )

        print('create datetime index with freq "w" and check if all dates are Sundays (default)')
        indexer = _trade_time_index('20200101', '20200201', freq='w', trade_days_only=False)
        print(f'the output is {indexer}')
        self.assertIsInstance(indexer, pd.DatetimeIndex)
        self.assertEqual(len(indexer), 4)
        self.assertTrue(
                all(day.day_name() == 'Sunday' for day in indexer)
        )

        print('create datetime index with freq "w-Fri" and check if all dates are Fridays')
        indexer = _trade_time_index('20200101', '20200201', freq='w-Fri', trade_days_only=False)
        print(f'the output is {indexer}')
        self.assertIsInstance(indexer, pd.DatetimeIndex)
        self.assertEqual(len(indexer), 5)
        self.assertTrue(
                all(day.day_name() == 'Friday' for day in indexer)
        )

        print('create datetime index with start/end/periods')
        print('when freq can be inferred')
        indexer = _trade_time_index(start='20200102', end='20200103', periods=49)
        print(f'the output is {indexer}')
        self.assertEqual(len(indexer), 9)
        self.assertEqual(list(indexer),
                         list(pd.to_datetime(['2020-01-02 09:30:00', '2020-01-02 10:00:00',
                                              '2020-01-02 10:30:00', '2020-01-02 11:00:00',
                                              '2020-01-02 11:30:00', '2020-01-02 13:30:00',
                                              '2020-01-02 14:00:00', '2020-01-02 14:30:00',
                                              '2020-01-02 15:00:00'])
                              )
                         )
        print('when freq can NOT be inferred')
        indexer = _trade_time_index(start='20200101', end='20200102', periods=50, trade_days_only=False)
        print(f'the output is {indexer}')
        self.assertEqual(len(indexer), 8)
        self.assertEqual(list(indexer),
                         list(pd.to_datetime(['2020-01-01 09:47:45.306122448',
                                              '2020-01-01 10:17:08.571428571',
                                              '2020-01-01 10:46:31.836734693',
                                              '2020-01-01 11:15:55.102040816',
                                              '2020-01-01 13:13:28.163265306',
                                              '2020-01-01 13:42:51.428571428',
                                              '2020-01-01 14:12:14.693877551',
                                              '2020-01-01 14:41:37.959183673'])
                              )
                         )

        print('create datetime index with start/periods/freq')
        indexer = _trade_time_index(start='20200101', freq='30min', periods=49, trade_days_only=False)
        print(f'the output is {indexer}')
        self.assertEqual(len(indexer), 9)
        self.assertEqual(list(indexer),
                         list(pd.to_datetime(['2020-01-01 09:30:00', '2020-01-01 10:00:00',
                                              '2020-01-01 10:30:00', '2020-01-01 11:00:00',
                                              '2020-01-01 11:30:00', '2020-01-01 13:30:00',
                                              '2020-01-01 14:00:00', '2020-01-01 14:30:00',
                                              '2020-01-01 15:00:00'])
                              )
                         )

        print('test false input')

    def test_freq_manipulations(self):
        """ 测试频率操作函数"""
        print('test parse_freq_string function')
        self.assertEqual(parse_freq_string('t'), (1, 'T', ''))
        self.assertEqual(parse_freq_string('min'), (1, '1MIN', ''))
        self.assertEqual(parse_freq_string('15min'), (1, '15MIN', ''))
        self.assertEqual(parse_freq_string('15min', std_freq_only=True), (15, 'MIN', ''))
        self.assertEqual(parse_freq_string('75min'), (5, '15MIN', ''))
        self.assertEqual(parse_freq_string('90min'), (3, '30MIN', ''))
        self.assertEqual(parse_freq_string('60min'), (2, '30MIN', ''))
        self.assertEqual(parse_freq_string('H'), (1, 'H', ''))
        self.assertEqual(parse_freq_string('14d'), (14, 'D', ''))
        self.assertEqual(parse_freq_string('2w-Fri'), (2, 'W', 'FRI'))
        self.assertEqual(parse_freq_string('w'), (1, 'W', ''))
        self.assertEqual(parse_freq_string('wrong_input'), (None, None, None))

        print('test get_main_freq_level function')
        self.assertEqual(get_main_freq_level('5min'), 90)
        self.assertEqual(get_main_freq_level('15min'), 80)
        self.assertEqual(get_main_freq_level('w'), 40)
        self.assertIsNone(get_main_freq_level('wrong_input'), None)

        print('test next_main_freq function')
        self.assertEqual(next_main_freq('5min', 'up'), '1MIN')
        self.assertEqual(next_main_freq('w', 'up'), 'D')
        self.assertEqual(next_main_freq('m', 'up'), 'W')
        self.assertEqual(next_main_freq('w', 'down'), 'M')
        self.assertEqual(next_main_freq('m', 'down'), 'Q')
        self.assertEqual(next_main_freq('d', 'down'), 'W')
        self.assertEqual(next_main_freq('15min', 'down'), '30MIN')
        self.assertEqual(next_main_freq('30min', 'down'), 'H')

        print('test freq_dither function')
        self.assertEqual(freq_dither('d', ['15min', 'd', 'w', 'm']), 'D')
        self.assertEqual(freq_dither('3d', ['15min', 'd', 'w', 'm']), 'D')
        self.assertEqual(freq_dither('w', ['15min', 'd', 'w', 'm']), 'W')
        self.assertEqual(freq_dither('w-Fri', ['15min', 'd', 'w', 'm']), 'W')
        self.assertEqual(freq_dither('w-Fri', ['15min', 'd', 'm']), 'D')
        self.assertEqual(freq_dither('45min', ['5min', '15min', '30min', 'd', 'w', 'm']), '15MIN')
        self.assertEqual(freq_dither('40min', ['5min', '15min', '30min', 'd', 'w', 'm']), '5MIN')
        self.assertEqual(freq_dither('90min', ['5min', '15min', '30min', 'd', 'w', 'm']), '30MIN')
        self.assertEqual(freq_dither('90min', ['5min', '15min', 'd', 'w', 'm']), '15MIN')
        self.assertEqual(freq_dither('t', ['5min', '15min', '30min', 'd', 'w', 'm']), '5MIN')
        self.assertEqual(freq_dither('d', ['w', 'm', 'q']), 'W')
        self.assertEqual(freq_dither('d', ['m', 'q']), 'M')
        self.assertEqual(freq_dither('m', ['5min', '15min', '30min', 'd', 'w', 'q']), 'W')

    def test_insert_read_sys_table_data(self):
        # 测试正常情况下写入及读取表的数据
        test_order_data = {
                    'pos_id': 1,
                    'direction': 'buy',
                    'order_type': 'limit',
                    'qty': 100,
                    'price': 10.0,
                    'submitted_time': pd.to_datetime('20230220'),
                    'status': 'submitted',
        }
        test_result_data = {
            'order_id': 1,
            'filled_qty': 100,
            'price': 10.0,
            'transaction_fee': 0.0,
            'execution_time': pd.to_datetime('20230220'),
            'canceled_qty': 0,
            'delivery_amount': 0.0,
            'delivery_status': 'ND',
        }
        test_account_data = {
            'user_name': 'John Doe',
            'created_time': pd.to_datetime('20221223'),
            'cash_amount': 40000.0,
            'available_cash': 40000.0,
            'total_invest': 40000.0,
        }
        test_position = {
            'account_id': 1, 
            'symbol': '000001.SZ',
            'position': 'long',
            'qty': 100,
            'available_qty': 100.,
            'cost': 10.0,
        }
        test_shuffled_signal_data = {
            'pos_id': 1,
            'qty': 300,
            'status': 'filled',
            'order_type': 'market',
            'price': 15.0,
            'direction': 'sell',
            'submitted_time': pd.to_datetime('20230223'),
        }  # test if shuffled data can be inserted into database
        # 生成五条不同的模拟信号数据
        test_multiple_signal_data = [
            {
                'pos_id': 1,
                'direction': 'buy',
                'order_type': 'limit',
                'qty': 100,
                'price': 10.0,
                'submitted_time': pd.to_datetime('20230220'),
                'status': 'submitted',
            },
            {
                'pos_id': 2,
                'direction': 'buy',
                'order_type': 'limit',
                'qty': 200,
                'price': 10.0,
                'submitted_time': pd.to_datetime('20230220'),
                'status': 'submitted',
            },
            {
                'pos_id': 3,
                'direction': 'buy',
                'order_type': 'limit',
                'qty': 300,
                'price': 10.0,
                'submitted_time': pd.to_datetime('20230220'),
                'status': 'submitted',
            },
            {
                'pos_id': 4,
                'direction': 'buy',
                'order_type': 'limit',
                'qty': 400,
                'price': 10.0,
                'submitted_time': pd.to_datetime('20230220'),
                'status': 'submitted',
            },
            {
                'pos_id': 5,
                'direction': 'buy',
                'order_type': 'limit',
                'qty': 500,
                'price': 10.0,
                'submitted_time': pd.to_datetime('20230220'),
                'status': 'submitted',
            },
        ]
        test_multiple_result_data = [
            {
                'order_id': 1,
                'filled_qty': 100,
                'price': 10.0,
                'transaction_fee': 0.0,
                'execution_time': pd.to_datetime('20230220'),
                'canceled_qty': 0,
                'delivery_amount': 0.0,
                'delivery_status': 'ND',
            },
            {
                'order_id': 2,
                'filled_qty': 200,
                'price': 10.0,
                'transaction_fee': 0.0,
                'execution_time': pd.to_datetime('20230220'),
                'canceled_qty': 0,
                'delivery_amount': 0.0,
                'delivery_status': 'ND',
            },
            {
                'order_id': 3,
                'filled_qty': 300,
                'price': 10.0,
                'transaction_fee': 0.0,
                'execution_time': pd.to_datetime('20230221'),
                'canceled_qty': 0,
                'delivery_amount': 0.0,
                'delivery_status': 'ND',
            },
            {
                'order_id': 4,
                'filled_qty': 400,
                'price': 10.0,
                'transaction_fee': 0.0,
                'execution_time': pd.to_datetime('20230221'),
                'canceled_qty': 0,
                'delivery_amount': 0.0,
                'delivery_status': 'ND',
            },
            {
                'order_id': 5,
                'filled_qty': 500,
                'price': 10.0,
                'transaction_fee': 0.0,
                'execution_time': pd.to_datetime('20230221'),
                'canceled_qty': 0,
                'delivery_amount': 0.0,
                'delivery_status': 'ND',
            },

        ]
        test_multiple_account_data = [
            {
                'user_name': 'John Doe',
                'created_time': pd.to_datetime('20221223'),
                'cash_amount': 40000.0,
                'available_cash': 40000.0,
                'total_invest': 40000.0,
            },
            {
                'user_name': 'John Doe1',
                'created_time': pd.to_datetime('20221223'),
                'cash_amount': 40000.0,
                'available_cash': 40000.0,
                'total_invest': 40000.0,
            },
            {
                'user_name': 'John Doe2',
                'created_time': pd.to_datetime('20221221'),
                'cash_amount': 40000.0,
                'available_cash': 40000.0,
                'total_invest': 40000.0,
            },
            {
                'user_name': 'John Doe3',
                'created_time': pd.to_datetime('20221222'),
                'cash_amount': 40000.0,
                'available_cash': 40000.0,
                'total_invest': 40000.0,
            },
            {
                'user_name': 'John Doe4',
                'created_time': pd.to_datetime('20221224'),
                'cash_amount': 40000.0,
                'available_cash': 40000.0,
                'total_invest': 40000.0,
            },
        ]
        test_multiple_position = [
            {
                'account_id': 1,
                'symbol': '000001.SZ',
                'position': 'long',
                'qty': 100,
                'available_qty': 100.,
                'cost': 10.0,
            },
            {
                'account_id': 1,
                'symbol': '000002.SZ',
                'position': 'long',
                'qty': 200,
                'available_qty': 100.,
                'cost': 10.0,
            },
            {
                'account_id': 1,
                'symbol': '000003.SZ',
                'position': 'long',
                'qty': 300,
                'available_qty': 100.,
                'cost': 10.0,
            },
            {
                'account_id': 2,
                'symbol': '000004.SZ',
                'position': 'long',
                'qty': 400,
                'available_qty': 100.,
                'cost': 10.0,
            },
            {
                'account_id': 2,
                'symbol': '000005.SZ',
                'position': 'long',
                'qty': 500,
                'available_qty': 100.,
                'cost': 10.0,
            },
        ]

        sys_table_test_data = [
            test_account_data,
            test_position,
            test_order_data,
            test_result_data,
        ]
        sys_table_test_multiple_data = [
            test_multiple_account_data,
            test_multiple_position,
            test_multiple_signal_data,
            test_multiple_result_data,
        ]

        tables_to_be_tested = [
            'sys_op_live_accounts',
            'sys_op_positions',
            'sys_op_trade_orders',
            'sys_op_trade_results'
        ]
        test_kwargs_existed = [
            {'user_name': 'John Doe'},
            {'account_id': 1},
            {'direction': 'buy'},
            {'order_id': 1}
        ]
        test_kwargs_not_existed = [
            {'user_name': 'Not a user'},
            {'account_id': 999},
            {'direction': 'invalid_direction'},
            {'order_id': 999}
        ]
        test_kwargs_to_update = [
            {'user_name': 'new_user'},
            {'account_id': 3},
            {'direction': 'sell'},
            {'order_id': 3}
        ]

        datasources_to_be_tested = [
            self.ds_csv,
            self.ds_hdf,
            self.ds_fth,
            self.ds_db
        ]

        for table, data in zip(tables_to_be_tested, sys_table_test_data):
            print(f'\n=============================='
                  f'\ntest insert and read one piece of data...\n'
                  f'following table will be tested: {table}\n'
                  f'with data: {data}')
            for ds in datasources_to_be_tested:
                if ds.table_data_exists(table):
                    ds.drop_table_data(table)
                print(f'\n----------------------'
                      f'\ninserting into table {table}@{ds} with following data\n{data}')
                ds.insert_sys_table_data(table, **data)
                res = ds.read_sys_table_data(table, 1)
                print(f'following data are read from table {table}\n'
                      f'{res}\n')
                self.assertIsNotNone(res)
                for origin, read in zip(data.values(), res.values()):
                    print(f'origin: {origin}->{type(origin)}, read: {read}->{type(read)}')
                    if isinstance(origin, pd.Timestamp):
                        self.assertEqual(origin, pd.to_datetime(read))
                    else:
                        self.assertEqual(origin, read)
                # if ds.table_data_exists(table):
                #     ds.drop_table_data(table)
                print(f'write and read shuffled data')
                ds.insert_sys_table_data('sys_op_trade_orders', **test_shuffled_signal_data)
                last_id = ds.get_sys_table_last_id('sys_op_trade_orders')
                res = ds.read_sys_table_data('sys_op_trade_orders', record_id=last_id)
                print(f'following data are read from table "sys_table_trade_signal" with id = {last_id}\n'
                      f'{res}\n')
                self.assertIsNotNone(res)
                self.assertEqual(test_shuffled_signal_data['pos_id'], res['pos_id'])
                self.assertEqual(test_shuffled_signal_data['order_type'], res['order_type'])
                self.assertEqual(test_shuffled_signal_data['status'], res['status'])
                self.assertEqual(test_shuffled_signal_data['direction'], res['direction'])
                self.assertEqual(test_shuffled_signal_data['price'], res['price'])
                self.assertEqual(test_shuffled_signal_data['qty'], res['qty'])

            # 测试传入无效的id时是否引发KeyError异常
            print(f'test passing invalid id to read_sys_table_data')
            res = ds.read_sys_table_data(table, record_id=-1)
            self.assertIsNone(res)
            res = ds.read_sys_table_data(table, record_id=0)
            self.assertIsNone(res)
            res = ds.read_sys_table_data(table, record_id=999)
            self.assertIsNone(res)

            # 测试传入无效的表名时是否引发KeyError异常
            with self.assertRaises(KeyError):
                ds.read_sys_table_data('invalid_table')

            # 测试传入无效的kwargs时是否引发KeyError异常
            with self.assertRaises(KeyError):
                ds.read_sys_table_data('test_table', invalid_column='test')

            # 测试写入不正确的dict时是否返回错误
            print(f'test writing wrong data fields into table')
            with self.assertRaises(Exception):
                ds.insert_sys_table_data(
                    table,
                    **{
                        'wrong_key1': 'wrong_value',
                        'wrong_key2': 321,
                    }
                )

        # 测试读取指定id的记录
        # 循环使用所有的示例数据在所有的sys表上进行测试，测试覆盖所有的source_type
        # 首先在数据表中写入五条数据，每条数据稍有变化
        # 1，测试随机读取一条已经存在的数据，验证是否读取正确
        # 2，测试传入无效的id时是否返回None
        # 3，测试传入kwargs筛选数据，验证是否读取正确
        # 4，测试传入无效的kwargs时是否返回None
        # table: str, record_id: int=None, **kwargs
        for table, datas, kw, kwn, kwu in zip(
                tables_to_be_tested,
                sys_table_test_multiple_data,
                test_kwargs_existed,
                test_kwargs_not_existed,
                test_kwargs_to_update
        ):
            print(f'\n=============================='
                  f'\ntest insert and read specific data from table...\n'
                  f'following table will be tested: {table}\n'
                  f'with multiple data')
            for ds in datasources_to_be_tested:
                if ds.table_data_exists(table):
                    ds.drop_table_data(table)
                print(f'\n----------------------'
                      f'\ninserting multiple data into table {table}@{ds} ')
                for data in datas:
                    ds.insert_sys_table_data(table, **data)
                id_to_read = int(np.random.randint(5, size=(1,)))
                res = ds.read_sys_table_data(table, id_to_read + 1)
                print(f'\nreading data with "id = {id_to_read}"...\n'
                      f'following data are read from table {table}\n'
                      f'{res}\n')
                self.assertIsNotNone(res)
                for origin, read in zip(datas[id_to_read].values(), res.values()):
                    print(f'origin: {origin}->{type(origin)}, read: {read}->{type(read)}')
                    if isinstance(origin, pd.Timestamp):
                        self.assertEqual(origin, pd.to_datetime(read))
                    else:
                        self.assertEqual(origin, read)

                # 测试传入无效的id时是否返回None
                res = ds.read_sys_table_data(table, 100)
                self.assertIsNone(res)

                # 测试传入kwargs筛选数据，验证是否读取正确
                print(f'\nreading data with kwargs: {kw}...\n')
                res = ds.read_sys_table_data(table, **kw)
                self.assertIsNotNone(res)
                # 检查res是一个pd.DataFrame
                self.assertIsInstance(res, pd.DataFrame)
                # 检查res的kw列的值是否都相同且与kw的值相同
                self.assertTrue((res[kw.keys()].values == list(kw.values())).all())
                print(f'values read matches kwargs:\n{res[kw.keys()].values}\n{list(kw.values())}')

                # 测试传入不存在的kwargs时是否返回None
                print(f'\nreading data with not existed kwargs: {kwn}...\n')
                res = ds.read_sys_table_data(table, **kwn)
                self.assertIsNone(res)

                # 测试传入无效的kwargs是否返回None
                with self.assertRaises(KeyError):
                    ds.read_sys_table_data('test_table', invalid_column='test')

                # 测试update_sys_table_data后数据是否正确地更新
                print(f'\nupdating {table}@(id = {id_to_read}) with kwargs: {kwu}...\n')
                before = ds.read_sys_table_data(table, record_id=id_to_read + 1)
                ds.update_sys_table_data(table, record_id=id_to_read + 1, **kwu)
                after = ds.read_sys_table_data(table, record_id=id_to_read + 1)
                print(f'before update:\n{before}\nafter update:\n{after}')
                for bk_v, ak_v in zip(before.items(), after.items()):
                    if bk_v[0] in kwu.keys():
                        self.assertEqual(ak_v[1], kwu[bk_v[0]])
                    else:
                        if isinstance(bk_v[0], pd.Timestamp):
                            self.assertEqual(bk_v[1], pd.to_datetime(ak_v[1]))
                        else:
                            self.assertEqual(bk_v[1], ak_v[1])

                res = ds.read_sys_table_data(
                        table='sys_op_positions',
                        record_id=None,
                        account_id=1,
                        symbol='000001.SZ',
                        position='long',
                )
                print(f'res: {res}')

    def test_fetch_realtime_price_data(self):
        """ test datasource function fetch_realtime_price_data()"""
        res = self.ds_csv.fetch_realtime_price_data(
                table='stock_5min',
                channel='eastmoney',
                symbols=['000001.SZ', '000002.SZ'],
        )
        print(res)
        self.assertIsInstance(res, pd.DataFrame)


if __name__ == '__main__':
    unittest.main()
