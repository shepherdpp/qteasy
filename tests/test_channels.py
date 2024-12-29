# coding=utf-8
# ======================================
# File:     test_channels.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-12-25
# Desc:
#   Testing download data from different
# data channels for every possible data
# table in the test datasource.
# ======================================

import unittest

from qteasy.database import DataSource
from qteasy.data_channels import (
    TUSHARE_API_MAP,
    EASTMONEY_API_MAP,
    AKSHARE_API_MAP,
    fetch_history_table_data,
    fetch_realtime_price_data,
    _parse_list_args,
    _parse_datetime_args,
    _parse_trade_date_args,
    _parse_quarter_args,
    _parse_month_args,
    _parse_table_index_args,
)


class TestChannels(unittest.TestCase):

    def setUp(self):
        from qteasy import QT_CONFIG
        self.ds = DataSource(
            'db',
            host=QT_CONFIG['test_db_host'],
            port=QT_CONFIG['test_db_port'],
            user=QT_CONFIG['test_db_user'],
            password=QT_CONFIG['test_db_password'],
            db_name=QT_CONFIG['test_db_name']
        )
        print('test datasource created.')

    def test_channel_tushare(self):
        """testing downloading small piece of data and store them in self.test_ds"""

        # tables into which to download data are from TABLE_MASTERS,
        # but in the future, tables should be from data_channels
        all_tables = TUSHARE_API_MAP.keys()

        self.assertIsInstance(self.ds, DataSource)

        # if there already are tables existing in the datasource, drop them
        print('dropping tables in the test database...')
        for table in all_tables:
            if table == 'real_time':
                continue
            if self.ds.table_data_exists(table):
                # these data can be retained for further testing
                self.ds.drop_table_data(table)
                print(f'table {table} dropped.')
        print('tables dropped.')

        for table in all_tables:
            if table == 'real_time':
                continue

            # get all tables in the API mapping
            api_name = TUSHARE_API_MAP[table][0]
            arg_name = TUSHARE_API_MAP[table][1]
            arg_type = TUSHARE_API_MAP[table][2]
            arg_range = TUSHARE_API_MAP[table][3]

            print(f'downloading data for table: {table} with api: {api_name} and arg: {arg_name}')

            # parse the filling args and pick the first filling arg value from the range
            if arg_name == 'none':
                arg_name = None
                arg_value = None
            else:
                if arg_type == 'list':
                    from qteasy.utilfuncs import str_to_list
                    range_list = str_to_list(arg_range)
                    arg_value = range_list[0]
                elif arg_type == 'datetime':
                    arg_value = '20210226'
                elif arg_type == 'trade_date':
                    arg_value = '20210226'  # 这个交易日是特意选择的，因为它既是一个交易日，也同时是一周/一月内的最后一个交易日
                elif arg_type == 'quarter':
                    arg_value = '2020Q4'
                elif arg_type == 'month':
                    arg_value = '202102'
                elif arg_type == 'table_index' and arg_range == 'stock_basic':
                    arg_value = '000651.SZ'
                elif arg_type == 'table_index' and arg_range == 'index_basic':
                    arg_value = '000001.SH'
                elif arg_type == 'table_index' and arg_range == 'fund_basic':
                    arg_value = '531300.SH'
                elif arg_type == 'table_index' and arg_range == 'future_basic':
                    arg_value = 'IF2009.CCFX'
                elif arg_type == 'table_index' and arg_range == 'opt_basic':
                    arg_value = '10001234.SH'
                elif arg_type == 'table_index' and arg_range == 'ths_index_basic':
                    arg_value = '700031.TI'
                else:
                    raise ValueError('unexpected arg type:', arg_type)

            # build the args dict
            if arg_name is not None:
                kwargs = {arg_name: arg_value}
            else:
                kwargs = {}

            # add retry parameters to shorten test time
            kwargs['retry_count'] = 1

            try:
                dnld_data = fetch_history_table_data(table, channel='tushare', **kwargs)
                print(f'{len(dnld_data)} rows of data downloaded:\n{dnld_data.head()}')
            except Exception as e:
                print(f'error downloading data for table {table}: {e}')
                continue

            # clean up the data, making it ready to be written to the datasource
            from qteasy.database import get_built_in_table_schema, set_primary_key_frame
            columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
            ready_data = set_primary_key_frame(dnld_data, primary_keys, pk_dtypes)

            # write data to datasource
            self.ds.update_table_data(table, ready_data, merge_type='update')
            print('data written to database.')

    def test_arg_parsing(self):
        """testing parsing of filling args"""

        print('testing parsing list type args')
        arg_range = 'A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z'
        list_arg_filter = 'A, B, E'

        res = list(_parse_list_args(arg_range, list_arg_filter))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'E'])

        list_arg_filter = ['A', 'B', 'E']
        res = list(_parse_list_args(arg_range, ['A', 'B', 'E'], reversed=True))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['E', 'B', 'A'])

        list_arg_filter = 'A:E'
        res = list(_parse_list_args(arg_range, 'A:E', reversed=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C', 'D', 'E'])

        list_arg_filter = 'D:A'
        res = list(_parse_list_args(arg_range, 'D:A', reversed=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C', 'D'])

        list_arg_filter = None
        res = list(_parse_list_args(arg_range, None, reversed=True))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['Z', 'Y', 'X', 'W', 'V', 'U', 'T', 'S', 'R', 'Q', 'P', 'O', 'N', 'M', 'L', 'K',
                               'J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
        )

        list_arg_filter = 'A:C:P'
        res = list(_parse_list_args(arg_range, 'A:C:P', reversed=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C'])

        # testing error handling:
        with self.assertRaises(Exception):
            list(_parse_list_args(arg_range, ['A:Z:1'], reversed=False))
            list(_parse_list_args(arg_range, 35, reversed=False))

        print('testing parsing datetime type args')
        arg_range = '20210101'

        start, end = '20210201', '20210210'
        res = _parse_datetime_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210201', '20210202', '20210203', '20210204', '20210205', '20210206',
                               '20210207', '20210208', '20210209', '20210210'])

        start, end = '20201220', '20210105'
        res = _parse_datetime_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210101', '20210102', '20210103', '20210104', '20210105'])

        start, end = '20201220', '20210105'
        res = _parse_datetime_args(arg_range, start, end, reversed=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210105', '20210104', '20210103', '20210102', '20210101'])

        start, end = '20210110', '20210105'
        res = _parse_datetime_args(arg_range, start, end, reversed=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210110', '20210109', '20210108', '20210107', '20210106', '20210105'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_datetime_args(arg_range, 'not_a_date', '20201231')
            _parse_datetime_args(arg_range, '20210101', 20201231)

    def test_realtime_data(self):
        """testing downloading small piece of data and store them in self.test_ds"""

        # test acquiring real time data

        table = 'real_time'
        # get all tables in the API mapping
        print('downloading data for table:', table)
        dnld_data = fetch_realtime_price_data(channel='tushare', qt_code='000001.SZ')


if __name__ == '__main__':
    unittest.main()