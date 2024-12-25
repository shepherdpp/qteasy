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

    def test_tushare_APIs(self):
        """testing downloading small piece of data and store them in self.test_ds"""

        # tables into which to download data are from TABLE_MASTERS,
        # but in the future, tables should be from data_channels
        from qteasy.datatables import TABLE_MASTERS
        all_tables = TABLE_MASTERS.keys()

        self.assertIsInstance(self.ds, DataSource)

        for table in all_tables:
            schema = TABLE_MASTERS[table][0]
            desc = TABLE_MASTERS[table][1]
            usage = TABLE_MASTERS[table][2]

            if usage == 'sys':
                continue  # skip system tables

            # download data from tushare, currently use method from DataSource,
            # but in the future, use data_channels
            print(f'downloading data for table {table}-{desc} from tushare...')
            downloaded_data = self.ds.fetch_history_table_data(table, channel='tushare')
            total_rows = len(downloaded_data)
            print(f'downloaded {total_rows} rows of data for table {table}-{desc} from tushare.')
            total_written = self.ds.update_table_data(table, downloaded_data)
            print(f'written {total_written} rows of data for table {table}-{desc} to database.')


if __name__ == '__main__':
    unittest.main()