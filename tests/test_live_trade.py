# coding=utf-8
# ======================================
# File:     test_live_trade.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-02-20
# Desc:
#   Unittest for all functionalities
#   related to live trade.
# ======================================
import unittest

import os
import qteasy as qt
import pandas as pd
from pandas import Timestamp
import numpy as np

from qteasy.database import DataSource


class TestLiveTrade(unittest.TestCase):

    def setUp(self) -> None:
        """ execute before each test"""
        from qteasy import QT_ROOT_PATH
        self.qt_root_path = QT_ROOT_PATH
        self.data_test_dir = 'data_test/'
        # 测试数据不会放在默认的data路径下，以免与已有的文件混淆
        # 使用测试数据库进行除"test_get_history_panel()"以外的其他全部测试
        config = qt.QT_CONFIG
        self.ds_db = DataSource('db',
                                host=config['test_db_host'],
                                user=config['test_db_user'],
                                password=config['test_db_password'],
                                db_name=config['test_db_name'])
        self.ds_csv = DataSource('file', file_type='csv', file_loc=self.data_test_dir)
        self.ds_hdf = DataSource('file', file_type='hdf', file_loc=self.data_test_dir)
        self.ds_fth = DataSource('file', file_type='fth', file_loc=self.data_test_dir)

    def test_read_write_signals(self):
        """ test writing trade signals to trade_signal tables in all datasource types"""
        # TODO: implement this test case
        pass

    def test_read_write_results(self):
        """ test writing trade signal results into data tables in all datasource types"""
        # TODO: implement this test case
        pass

    def test_process_account_table(self):
        """ test basic update operation with account table in all datasource types"""
        # TODO: implement this test case
        pass

    def test_process_position_table(self):
        """ test basic operations with position table in all datasource types"""
        # TODO: implement this test case
        pass

    def test_signal_process(self):
        """ full process test of signal process in all datasource types"""
        # TODO: implement this test case
        pass

    def test_live_trade_functions(self):
        """ test all functions defined in live_trade

        this test case might be separated into multiple test cases
        """
        pass


if __name__ == '__main__':
    unittest.main()
