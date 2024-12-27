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

        # if there already are tables existing in the datasource, drop them
        all_tables = TUSHARE_API_MAP.keys()

        print('dropping tables in the test database...')
        for table in all_tables:
            if table == 'real_time':
                continue
            if self.ds.table_data_exists(table):
                self.ds.drop_table_data(table)
                print(f'table {table} dropped.')
        print('tables dropped.')

    def test_channel_tushare(self):
        """testing downloading small piece of data and store them in self.test_ds"""

        # tables into which to download data are from TABLE_MASTERS,
        # but in the future, tables should be from data_channels
        all_tables = TUSHARE_API_MAP.keys()

        self.assertIsInstance(self.ds, DataSource)

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
                elif arg_type == 'table_index' and arg_range == 'stock_basic':
                    arg_value = '000651.SZ'
                elif arg_type == 'table_index' and arg_range == 'index_basic':
                    arg_value = '000001.SH'
                elif arg_type == 'table_index' and arg_range == 'fund_basic':
                    arg_value = '531300.SH'
                elif arg_type == 'table_index' and arg_range == 'futures_basic':
                    arg_value = 'IF2009.CCFX'
                elif arg_type == 'table_index' and arg_range == 'option_basic':
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

    def test_realtime_data(self):
        """testing downloading small piece of data and store them in self.test_ds"""

        # test acquiring real time data

        table = 'real_time'
        # get all tables in the API mapping
        print('downloading data for table:', table)
        dnld_data = fetch_realtime_price_data(channel='tushare', qt_code='000001.SZ')


if __name__ == '__main__':
    unittest.main()