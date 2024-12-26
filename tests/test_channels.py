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

    def test_channel_tushare(self):
        """testing downloading small piece of data and store them in self.test_ds"""

        # tables into which to download data are from TABLE_MASTERS,
        # but in the future, tables should be from data_channels
        from qteasy.data_channels import TUSHARE_API_MAP
        all_tables = TUSHARE_API_MAP.keys()

        self.assertIsInstance(self.ds, DataSource)

        for table in all_tables:
            # get all tables in the API mapping
            print('downloading data for table:', table)


if __name__ == '__main__':
    unittest.main()