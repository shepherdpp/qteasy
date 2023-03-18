# coding=utf-8
# ======================================
# File:     test_trading.py
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

from qteasy.trading import parse_pt_signals, parse_ps_signals, parse_vs_signals, itemize_trade_signals
from qteasy.trading import parse_trade_signal
from qteasy.trading import new_account, get_account, update_account, update_account_balance, get_or_create_position
from qteasy.trading import update_position, get_account_positions, check_account_availability
from qteasy.trading import check_position_availability, record_trade_signal, update_trade_signal, read_trade_signal
from qteasy.trading import query_trade_signals, submit_signal, output_trade_signal, get_position_by_id
from qteasy.trading import get_position_ids, read_trade_signal_detail, save_parsed_trade_signals
from qteasy.trading import get_account_cash_availabilities, get_account_position_availabilities, submit_signal
from qteasy.trading import write_trade_result, read_trade_result_by_id, read_trade_results_by_signal_id


class TestLiveTrade(unittest.TestCase):

    def setUp(self) -> None:
        """ execute before each test"""
        from qteasy import QT_ROOT_PATH
        self.qt_root_path = QT_ROOT_PATH
        self.data_test_dir = 'data_test/'
        # 创建一个专用的测试数据源，以免与已有的文件混淆，不需要测试所有的数据源，因为相关测试在test_datasource中已经完成
        self.test_ds = DataSource('file', file_type='csv', file_loc=self.data_test_dir)
        # 清空测试数据源中的所有相关表格数据
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_signals', 'sys_op_trade_signals']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)

    # test foundational functions related to database info read and write
    def test_create_and_get_account(self):
        """ test new_account function """
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        # test new_account with simple account info
        user_name = 'test_user'
        cash_amount = 10000.0
        account_id = new_account(user_name, cash_amount, data_source=self.test_ds)
        print(f'account created, id: {account_id}')
        self.assertEqual(account_id, 1)
        # add two more accounts
        new_account('test_user2', 20000, data_source=self.test_ds)
        new_account('test_user3', 30000, data_source=self.test_ds)
        # test get_account
        account = get_account(2, data_source=self.test_ds)
        self.assertEqual(account['user_name'], 'test_user2')
        self.assertEqual(account['cash_amount'], 20000.0)
        self.assertEqual(account['available_cash'], 20000.0)
        # test add account with negative cash amount
        with self.assertRaises(ValueError):
            new_account('test_user4', -10000, data_source=self.test_ds)
        # test get account with non-existing account id
        with self.assertRaises(RuntimeError):
            get_account(4, data_source=self.test_ds)

    def test_update_account(self):
        """ test update_account function """
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        # read all accounts from datasource and modify the username
        new_account('test_user', 10000, data_source=self.test_ds)
        new_account('test_user2', 20000, data_source=self.test_ds)
        account = get_account(1, data_source=self.test_ds)
        self.assertEqual(account['user_name'], 'test_user')
        update_account(1, data_source=self.test_ds, user_name='test_user1')
        account = get_account(1, data_source=self.test_ds)
        self.assertEqual(account['user_name'], 'test_user1')
        update_account(2, data_source=self.test_ds, user_name='new_user2')
        account = get_account(2, data_source=self.test_ds)
        self.assertEqual(account['user_name'], 'new_user2')
        # test update account with non-existing account id
        with self.assertRaises(KeyError):
            update_account(4, data_source=self.test_ds, user_name='test_user4')
        # update account balance and available cash
        update_account_balance(1, data_source=self.test_ds, cash_amount_change=-2000.0, available_cash_change=-2000.0)
        self.assertEqual(get_account(1, data_source=self.test_ds)['cash_amount'], 8000.0)
        self.assertEqual(get_account(1, data_source=self.test_ds)['available_cash'], 8000.0)
        update_account_balance(1, data_source=self.test_ds, cash_amount_change=1000.0, available_cash_change=1000.0)
        self.assertEqual(get_account(1, data_source=self.test_ds)['cash_amount'], 9000.0)
        self.assertEqual(get_account(1, data_source=self.test_ds)['available_cash'], 9000.0)

        # update account balance and available cash with non-existing account id
        with self.assertRaises(RuntimeError):
            update_account_balance(4, data_source=self.test_ds, cash_amount_change=1000.0, available_cash_change=1000.0)

        # update so that cash balance is wrong (negative or available cash is more than cash amount)
        with self.assertRaises(RuntimeError):
            update_account_balance(1, data_source=self.test_ds, cash_amount_change=-90000.0, available_cash_change=0.0)
            update_account_balance(1, data_source=self.test_ds, cash_amount_change=0.0, available_cash_change=-90000.0)
            update_account_balance(1, data_source=self.test_ds, cash_amount_change=0.0, available_cash_change=90000.0)

    def test_create_and_get_position(self):
        """ test new_position function """
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        # create new accounts and new positions
        new_account('test_user', 10000, data_source=self.test_ds)
        new_account('test_user2', 20000, data_source=self.test_ds)
        pos_id = get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 1)
        pos_id = get_or_create_position(1, 'AAPL', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 2)
        pos_id = get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        print(position)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'AAPL')
        self.assertEqual(position['position'], 'long')
        self.assertEqual(position['qty'], 0)
        pos_id = get_or_create_position(1, 'AAPL', 'short', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'AAPL')
        self.assertEqual(position['position'], 'short')
        self.assertEqual(position['qty'], 0)
        # add more positions to account 2
        get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'AAPL', 'short', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'short', data_source=self.test_ds)
        # test get_or_create_position with non-existing account id
        with self.assertRaises(RuntimeError):
            get_or_create_position(4, 'AAPL', 'long', data_source=self.test_ds)
        # test get_or_create_position with incorrect symbol type and direction type/value
        with self.assertRaises(TypeError):
            get_or_create_position(1, 123, 'long', data_source=self.test_ds)
            get_or_create_position(1, 'AAPL', 123, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            get_or_create_position(1, 'AAPL', 'long123', data_source=self.test_ds)

        # test get_position_id function
        pos_id = get_position_ids(1, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, [1])
        pos_id = get_position_ids(1, 'AAPL', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, [2])
        # test get_position_id with non-existing account id
        self.assertEqual(get_position_ids(4, 'AAPL', 'long', data_source=self.test_ds), [])
        # test get_position_id with incorrect symbol type and direction type/value
        self.assertEqual(get_position_ids(1, 123, 'long', data_source=self.test_ds), [])
        self.assertEqual(get_position_ids(1, 'AAPL', 123, data_source=self.test_ds), [])
        self.assertEqual(get_position_ids(1, 'AAPL', 'long123', data_source=self.test_ds), [])

        # test get_position_by_id function
        position = get_position_by_id(1, data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'AAPL')
        self.assertEqual(position['position'], 'long')
        self.assertEqual(position['qty'], 0)
        position = get_position_by_id(2, data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'AAPL')
        self.assertEqual(position['position'], 'short')
        self.assertEqual(position['qty'], 0)
        # test get_position_by_id with non-existing position id
        with self.assertRaises(RuntimeError):
            get_position_by_id(999, data_source=self.test_ds)

        # test get all positions with get_account_positions()
        positions = get_account_positions(1, data_source=self.test_ds)
        print(positions)
        self.assertIsInstance(positions, pd.DataFrame)
        self.assertEqual(len(positions), 2)
        self.assertEqual(positions.loc[1]['account_id'], 1)
        self.assertEqual(positions.loc[1]['symbol'], 'AAPL')
        self.assertEqual(positions.loc[1]['position'], 'long')
        self.assertEqual(positions.loc[1]['qty'], 0)
        self.assertEqual(positions.loc[2]['account_id'], 1)
        self.assertEqual(positions.loc[2]['symbol'], 'AAPL')
        self.assertEqual(positions.loc[2]['position'], 'short')
        self.assertEqual(positions.loc[2]['qty'], 0)
        position = get_account_positions(2, data_source=self.test_ds)
        print(position)
        self.assertIsInstance(position, pd.DataFrame)
        self.assertEqual(len(position), 4)
        self.assertEqual(position.loc[3]['account_id'], 2)
        self.assertEqual(position.loc[3]['symbol'], 'AAPL')
        self.assertEqual(position.loc[3]['position'], 'long')
        self.assertEqual(position.loc[3]['qty'], 0)
        self.assertEqual(position.loc[4]['account_id'], 2)
        self.assertEqual(position.loc[4]['symbol'], 'AAPL')
        self.assertEqual(position.loc[4]['position'], 'short')
        self.assertEqual(position.loc[4]['qty'], 0)
        self.assertEqual(position.loc[5]['account_id'], 2)
        self.assertEqual(position.loc[5]['symbol'], 'GOOG')
        self.assertEqual(position.loc[5]['position'], 'long')
        self.assertEqual(position.loc[5]['qty'], 0)
        self.assertEqual(position.loc[6]['account_id'], 2)
        self.assertEqual(position.loc[6]['symbol'], 'GOOG')
        self.assertEqual(position.loc[6]['position'], 'short')
        self.assertEqual(position.loc[6]['qty'], 0)

    def test_update_position(self):
        """ test update_position function """
        # clear existing accounts and positions, add test accounts and positions
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        # create new test accounts and new positions
        new_account(user_name='test_user1', cash_amount=100000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=100000, data_source=self.test_ds)
        pos_id = get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 1)
        pos_id = get_or_create_position(1, 'AAPL', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 2)
        pos_id = get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 3)
        pos_id = get_or_create_position(2, 'AAPL', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 4)
        pos_id = get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 5)
        pos_id = get_or_create_position(2, 'GOOG', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 6)
        # test update_position qty and available qty
        update_position(1, data_source=self.test_ds, qty_change=100)
        update_position(2, data_source=self.test_ds, qty_change=300)
        # check updated positions
        pos_id = get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 100)
        self.assertEqual(position['available_qty'], 0)
        pos_id = get_or_create_position(1, 'AAPL', 'short', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 0)
        # update qty and available qty in the same time
        update_position(3, data_source=self.test_ds, qty_change=200, available_qty_change=100)
        update_position(4, data_source=self.test_ds, qty_change=300, available_qty_change=300)
        # check updated positions
        pos_id = get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 200)
        self.assertEqual(position['available_qty'], 100)
        pos_id = get_or_create_position(2, 'AAPL', 'short', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 300)
        # update qty and available qty on previous positions
        update_position(3, data_source=self.test_ds, qty_change=100, available_qty_change=-100)
        update_position(4, data_source=self.test_ds, qty_change=300, available_qty_change=100)
        # check updated positions
        pos_id = get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 0)
        pos_id = get_or_create_position(2, 'AAPL', 'short', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 600)
        self.assertEqual(position['available_qty'], 400)

        # update qty and available qty with bad values
        with self.assertRaises(RuntimeError):
            update_position(3, data_source=self.test_ds, qty_change=-400, available_qty_change=100)
        with self.assertRaises(RuntimeError):
            update_position(4, data_source=self.test_ds, qty_change=300, available_qty_change=-500)
        with self.assertRaises(TypeError):
            update_position(5, data_source=self.test_ds, qty_change='not a number', available_qty_change=100)
        with self.assertRaises(TypeError):
            update_position(6, data_source=self.test_ds, qty_change=300, available_qty_change='not a number')

        # update position with bad pos_id
        with self.assertRaises(RuntimeError):
            update_position(0, data_source=self.test_ds, qty_change=100, available_qty_change=100)
        with self.assertRaises(RuntimeError):
            update_position(-1, data_source=self.test_ds, qty_change=100, available_qty_change=100)
        with self.assertRaises(TypeError):
            update_position('not a number', data_source=self.test_ds, qty_change=100, available_qty_change=100)
        with self.assertRaises(ValueError):
            update_position(None, data_source=self.test_ds, qty_change=100, available_qty_change=100)
        with self.assertRaises(RuntimeError):
            update_position(100, data_source=self.test_ds, qty_change=100, available_qty_change=100)

    # test 2nd foundational function: check_account_availability / check_position_availability
    def test_check_availability(self):
        """ test check_account_availability and position availability functions """
        # clear existing accounts and positions, add test accounts and positions
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        # add test accounts
        new_account(user_name='test_user1', cash_amount=100000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=100000, data_source=self.test_ds)
        # add test positions
        get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'AAPL', 'short', data_source=self.test_ds)
        get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'AAPL', 'short', data_source=self.test_ds)
        get_or_create_position(2, 'MSFT', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'MSFT', 'short', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'short', data_source=self.test_ds)
        # set cash amount and available amounts for test accounts
        update_account_balance(1, data_source=self.test_ds, cash_amount_change=100000, available_cash_change=100000)
        update_account_balance(2, data_source=self.test_ds, cash_amount_change=200000, available_cash_change=200000)
        # set position qty and available qty for test positions
        update_position(1, data_source=self.test_ds, qty_change=100, available_qty_change=100)
        update_position(2, data_source=self.test_ds, qty_change=200, available_qty_change=200)
        update_position(3, data_source=self.test_ds, qty_change=300, available_qty_change=300)
        update_position(4, data_source=self.test_ds, qty_change=400, available_qty_change=400)
        update_position(5, data_source=self.test_ds, qty_change=500, available_qty_change=500)
        update_position(6, data_source=self.test_ds, qty_change=600, available_qty_change=600)
        update_position(7, data_source=self.test_ds, qty_change=700, available_qty_change=700)
        update_position(8, data_source=self.test_ds, qty_change=800, available_qty_change=800)

        # test check_account_availability function
        res = check_account_availability(1, 10000, data_source=self.test_ds)
        self.assertEqual(res, 1.0)
        res = check_account_availability(1, 100000, data_source=self.test_ds)
        self.assertEqual(res, 1.0)
        res = check_account_availability(1, 400000, data_source=self.test_ds)
        self.assertEqual(res, 0.5)
        res = check_account_availability(2, 1000000, data_source=self.test_ds)
        self.assertEqual(res, 0.3)

        # test check_account_availability function with bad parameters
        with self.assertRaises(TypeError):
            check_account_availability('not an id', 10000, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            check_account_availability(None, 10000, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_account_availability(0, 10000, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_account_availability(-1, 10000, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            check_account_availability(1, 'not a number', data_source=self.test_ds)
        with self.assertRaises(TypeError):
            check_account_availability(1, None, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_account_availability(1, -10000, data_source=self.test_ds)

        # test check_position_availability function
        res = check_position_availability(1, 'AAPL', 'long', 100, data_source=self.test_ds)
        self.assertEqual(res, 1.0)
        res = check_position_availability(1, 'AAPL', 'long', 1000, data_source=self.test_ds)
        self.assertEqual(res, 0.1)
        res = check_position_availability(1, 'AAPL', 'short', 400, data_source=self.test_ds)
        self.assertEqual(res, 0.5)
        res = check_position_availability(1, 'AAPL', 'short', 1000, data_source=self.test_ds)
        self.assertEqual(res, 0.2)
        res = check_position_availability(1, 'AAPL', 'short', 0, data_source=self.test_ds)
        self.assertEqual(res, 1)
        # test check_position_availability function with not existing position
        with self.assertRaises(RuntimeError):
            res = check_position_availability(1, 'MSFT', 'long', 100, data_source=self.test_ds)

        # test check_position_availability function with bad parameters
        with self.assertRaises(RuntimeError):
            check_position_availability('not an id', 'AAPL', 'long', 100, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(None, 'AAPL', 'long', 100, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(0, 'AAPL', 'long', 100, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(-1, 'AAPL', 'long', 100, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(1, 1, 'long', 100, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(1, None, 'long', 100, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(1, 'AAPL', 1, 100, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(1, 'AAPL', None, 100, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            check_position_availability(1, 'AAPL', 'long', 'not a number', data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(1, 'AAPL', 'long', None, data_source=self.test_ds)
        with self.assertRaises(RuntimeError):
            check_position_availability(1, 'AAPL', 'long', -100, data_source=self.test_ds)

    def test_get_account_cash_and_position_availabilities(self):
        """ test function get_account_cash_availabilities and get_account_position_availabilities """
        # clear existing accounts and positions, add test accounts and positions
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        # create new test accounts and new positions
        new_account(user_name='test_user1', cash_amount=100000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=100000, data_source=self.test_ds)
        pos_id = get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 1)
        pos_id = get_or_create_position(1, 'GOOG', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 2)
        pos_id = get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 3)
        pos_id = get_or_create_position(2, 'MSFT', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 4)
        pos_id = get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 5)
        pos_id = get_or_create_position(2, 'AMZN', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 6)
        # set up available cash and positions
        update_account_balance(1, data_source=self.test_ds, cash_amount_change=0, available_cash_change=-20000)
        update_account_balance(2, data_source=self.test_ds, cash_amount_change=0, available_cash_change=-50000)
        update_position(1, data_source=self.test_ds, qty_change=1000, available_qty_change=1000)
        update_position(2, data_source=self.test_ds, qty_change=1000, available_qty_change=300)
        update_position(3, data_source=self.test_ds, qty_change=1000, available_qty_change=500)
        update_position(4, data_source=self.test_ds, qty_change=1000, available_qty_change=700)
        update_position(5, data_source=self.test_ds, qty_change=1000, available_qty_change=1000)
        update_position(6, data_source=self.test_ds, qty_change=1000, available_qty_change=600)

        # test get_account_cash_availabilities function
        res = get_account_cash_availabilities(account_id=1, data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], 100000)
        self.assertEqual(res[1], 80000)
        res = get_account_cash_availabilities(account_id=2, data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], 100000)
        self.assertEqual(res[1], 50000)

        # test get_account_position_availabilities function
        res = get_account_position_availabilities(account_id=1, shares=['AAPL', 'GOOG'], data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 2)
        self.assertIsInstance(res[0], np.ndarray)
        self.assertIsInstance(res[1], np.ndarray)
        self.assertEqual(res[0].shape, (2,))
        self.assertEqual(res[1].shape, (2,))
        print(f'get_account_position_availabilities result: {res}')
        self.assertTrue(np.allclose(res[0], np.array([1000, -1000])))
        self.assertTrue(np.allclose(res[1], np.array([1000, -300])))
        res = get_account_position_availabilities(account_id=2, shares=['AAPL', 'GOOG', 'MSFT', 'AMZN'],
                                                  data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 2)
        self.assertIsInstance(res[0], np.ndarray)
        self.assertIsInstance(res[1], np.ndarray)
        self.assertEqual(res[0].shape, (4,))
        self.assertEqual(res[1].shape, (4,))
        print(f'get_account_position_availabilities result: {res}')
        self.assertTrue(np.allclose(res[0], np.array([1000, 1000, -1000, -1000])))
        self.assertTrue(np.allclose(res[1], np.array([500, 1000, -700, -600])))
        res = get_account_position_availabilities(account_id=2, shares=['AAPL', 'FB', 'MSFT', 'AMZN', '000001'],
                                                    data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 2)
        self.assertIsInstance(res[0], np.ndarray)
        self.assertIsInstance(res[1], np.ndarray)
        self.assertEqual(res[0].shape, (5,))
        self.assertEqual(res[1].shape, (5,))
        print(f'get_account_position_availabilities result: {res}')
        self.assertTrue(np.allclose(res[0], np.array([1000, 0, -1000, -1000, 0])))
        self.assertTrue(np.allclose(res[1], np.array([500, 0, -700, -600, 0])))
        res = get_account_position_availabilities(account_id=2, data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 2)
        self.assertIsInstance(res[0], np.ndarray)
        self.assertIsInstance(res[1], np.ndarray)
        self.assertEqual(res[0].shape, (4,))
        print(f'get_account_position_availabilities result: {res}')
        self.assertTrue(np.allclose(res[0], np.array([1000, -1000, 1000, -1000])))
        self.assertTrue(np.allclose(res[1], np.array([500, -700, 1000, -600])))

    # test foundational functions related to signal generation and submission
    def test_record_read_and_update_signal(self):
        """ test record_and_read_signal function """
        # clear tables in test datasource if they existed
        if self.test_ds.table_data_exists('sys_op_trade_signals'):
            self.test_ds.drop_table_data('sys_op_trade_signals')
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')

        # writing test accounts and positions
        new_account('test_user', 100000, data_source=self.test_ds)
        get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'MSFT', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'GOOG', 'long', data_source=self.test_ds)
        # test recording and reading signals
        test_signal = {
            'pos_id': 1,
            'direction': 'buy',
            'order_type': 'market',
            'qty': 300,
            'price': 10.0,
            'submitted_time': None,
            'status': 'created',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id': 2,
            'direction': 'buy',
            'order_type': 'market',
            'qty': 200,
            'price': 10.0,
            'submitted_time': None,
            'status': 'created',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id': 3,
            'direction': 'sell',
            'order_type': 'market',
            'qty': 100,
            'price': 10.0,
            'submitted_time': None,
            'status': 'created',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        signal = read_trade_signal(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        signal = read_trade_signal(2, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 2)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 200)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        signal = read_trade_signal(3, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 3)
        self.assertEqual(signal['direction'], 'sell')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 100)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        # test record signal with bad input
        with self.assertRaises(TypeError):
            record_trade_signal(None, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            record_trade_signal(1, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            record_trade_signal('test', data_source=self.test_ds)
        bad_signal = {
            'account_id': 'a',
            'pos_id': 'a',
            'direction': 'buy',
            'order_type': 'market',
            'qty': 300,
            'price': 10.0,
            'submitted_time': None,
        }
        with self.assertRaises(TypeError):
            record_trade_signal(bad_signal, data_source=self.test_ds)
        bad_signal = {
            'account_id': 1,
            'pos_id': 1,
            'direction': 'buy',
            'order_type': 'market',
            'qty': -300,
            'price': -10.0,
            'status': 'created',
        }
        with self.assertRaises(RuntimeError):
            record_trade_signal(bad_signal, data_source=self.test_ds)
        # test read signal with bad input
        # self.assertIsNone(read_trade_signal(None, data_source=self.test_ds))  # will return all signals
        with self.assertRaises(TypeError):
            read_trade_signal(1.0, data_source=self.test_ds)
            read_trade_signal('test', data_source=self.test_ds)
        self.assertIsNone(read_trade_signal(-1, data_source=self.test_ds))

        # test update signal
        update_trade_signal(1, data_source=self.test_ds, status='submitted')
        signal = read_trade_signal(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'submitted')
        update_trade_signal(1, status='partial-filled', data_source=self.test_ds)
        signal = read_trade_signal(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'partial-filled')
        update_trade_signal(1, status='filled', data_source=self.test_ds)
        signal = read_trade_signal(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'filled')
        update_trade_signal(2, status='canceled', data_source=self.test_ds)
        signal = read_trade_signal(2, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 2)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 200)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        update_trade_signal(2, status='submitted', data_source=self.test_ds)
        signal = read_trade_signal(2, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 2)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 200)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'submitted')

        # test read trade signal details
        signal = read_trade_signal_detail(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['symbol'], 'AAPL')
        self.assertEqual(signal['position'], 'long')
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'filled')
        signal = read_trade_signal_detail(2, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 2)
        self.assertEqual(signal['symbol'], 'MSFT')
        self.assertEqual(signal['position'], 'long')
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 200)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'submitted')
        signal = read_trade_signal_detail(3, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 3)
        self.assertEqual(signal['symbol'], 'GOOG')
        self.assertEqual(signal['position'], 'long')
        self.assertEqual(signal['direction'], 'sell')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 100)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        # return None if no signal found
        signal = read_trade_signal_detail(4, data_source=self.test_ds)
        self.assertIs(signal, None)
        # test read trade signal details with bad input
        with self.assertRaises(TypeError):
            read_trade_signal_detail('1', data_source=self.test_ds)
            read_trade_signal_detail(-1, data_source=self.test_ds)
            read_trade_signal_detail(0, data_source=self.test_ds)
            read_trade_signal_detail(999, data_source=self.test_ds)
            read_trade_signal_detail(1.0, data_source=self.test_ds)

        # test update bad status
        with self.assertRaises(RuntimeError):
            update_trade_signal(1, status='test', data_source=self.test_ds, raise_if_status_wrong=True)
            update_trade_signal(1, status='created', data_source=self.test_ds, raise_if_status_wrong=True)
            update_trade_signal(1, status='submitted', data_source=self.test_ds, raise_if_status_wrong=True)
            update_trade_signal(1, status='partial-filled', data_source=self.test_ds, raise_if_status_wrong=True)
            update_trade_signal(1, status='filled', data_source=self.test_ds, raise_if_status_wrong=True)
        self.assertIsNone(
                update_trade_signal(1, status='test', data_source=self.test_ds, raise_if_status_wrong=False)
        )
        self.assertIsNone(
                update_trade_signal(1, status='created', data_source=self.test_ds, raise_if_status_wrong=False)
        )
        self.assertIsNone(
                update_trade_signal(1, status='submitted', data_source=self.test_ds, raise_if_status_wrong=False)
        )
        self.assertIsNone(
                update_trade_signal(1, status='partial-filled', data_source=self.test_ds, raise_if_status_wrong=False)
        )
        self.assertIsNone(
                update_trade_signal(1, status='filled', data_source=self.test_ds, raise_if_status_wrong=False)
        )

        # test update bad signal id
        with self.assertRaises(TypeError):
            update_trade_signal('test', status='submitted', data_source=self.test_ds)

    def test_query_trade_signals(self):
        """ test query_trade_signals function """
        # clear tables in test datasource if they existed
        if self.test_ds.table_data_exists('sys_op_trade_signals'):
            self.test_ds.drop_table_data('sys_op_trade_signals')
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')

        # writing test accounts and positions
        new_account('test_user1', 100000, data_source=self.test_ds)
        new_account('test_user2', 300000, data_source=self.test_ds)
        get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'MSFT', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'GOOG', 'long', data_source=self.test_ds)
        # test recording and reading signals
        test_signal = {
            'pos_id':         1,
            'direction':      'buy',
            'order_type':     'market',
            'qty':            300,
            'price':          10.0,
            'submitted_time': None,
            'status':         'created',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'buy',
            'order_type':     'market',
            'qty':            200,
            'price':          10.0,
            'submitted_time': None,
            'status':         'submitted',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         3,
            'direction':      'sell',
            'order_type':     'market',
            'qty':            100,
            'price':          10.0,
            'submitted_time': None,
            'status':         'filled',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'buy',
            'order_type':     'market',
            'qty':            300,
            'price':          15.0,
            'submitted_time': None,
            'status':         'submitted',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         3,
            'direction':      'buy',
            'order_type':     'market',
            'qty':            500,
            'price':          20.0,
            'submitted_time': None,
            'status':         'canceled',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         3,
            'direction':      'sell',
            'order_type':     'market',
            'qty':            200,
            'price':          20.0,
            'submitted_time': None,
            'status':         'partial-filled',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'sell',
            'order_type':     'market',
            'qty':            350,
            'price':          12.5,
            'submitted_time': None,
            'status':         'partial-filled',
        }
        record_trade_signal(test_signal, data_source=self.test_ds)

        # test query all signals for a symbol and direction
        signals = query_trade_signals(1, symbol='AAPL', position='long', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals['pos_id'].values[0], 1)
        self.assertEqual(signals['direction'].values[0], 'buy')
        self.assertEqual(signals['qty'].values[0], 300)
        self.assertEqual(signals['price'].values[0], 10.0)
        self.assertEqual(signals['status'].values[0], 'created')
        signals = query_trade_signals(1, symbol='GOOG', position='long', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 3)
        self.assertEqual(signals['pos_id'].values[0], 3)
        self.assertEqual(signals['direction'].values[0], 'sell')
        self.assertEqual(signals['qty'].values[0], 100)
        self.assertEqual(signals['price'].values[0], 10.0)
        self.assertEqual(signals['status'].values[0], 'filled')
        signals = query_trade_signals(1, symbol='GOOG', status='filled', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals['pos_id'].values[0], 3)
        self.assertEqual(signals['direction'].values[0], 'sell')
        self.assertEqual(signals['qty'].values[0], 100)
        self.assertEqual(signals['price'].values[0], 10.0)
        self.assertEqual(signals['status'].values[0], 'filled')
        signals = query_trade_signals(1, symbol='GOOG', status='canceled', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals['pos_id'].values[0], 3)
        self.assertEqual(signals['direction'].values[0], 'buy')
        self.assertEqual(signals['qty'].values[0], 500)
        self.assertEqual(signals['price'].values[0], 20.0)
        self.assertEqual(signals['status'].values[0], 'canceled')
        signals = query_trade_signals(2, symbol='MSFT', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 3)
        self.assertEqual(signals['pos_id'].values[0], 2)
        self.assertEqual(signals['direction'].values[0], 'buy')
        self.assertEqual(signals['qty'].values[0], 200)
        self.assertEqual(signals['price'].values[0], 10.0)
        self.assertEqual(signals['status'].values[0], 'submitted')
        self.assertEqual(signals['pos_id'].values[1], 2)
        self.assertEqual(signals['direction'].values[1], 'buy')
        self.assertEqual(signals['qty'].values[1], 300)
        self.assertEqual(signals['price'].values[1], 15.0)
        self.assertEqual(signals['status'].values[1], 'submitted')
        self.assertEqual(signals['pos_id'].values[2], 2)
        self.assertEqual(signals['direction'].values[2], 'sell')
        self.assertEqual(signals['qty'].values[2], 350)
        self.assertEqual(signals['price'].values[2], 12.5)
        self.assertEqual(signals['status'].values[2], 'partial-filled')
        signals = query_trade_signals(1, status='partial-filled', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals['pos_id'].values[0], 3)
        self.assertEqual(signals['direction'].values[0], 'sell')
        self.assertEqual(signals['qty'].values[0], 200)
        self.assertEqual(signals['price'].values[0], 20.0)
        self.assertEqual(signals['status'].values[0], 'partial-filled')
        signals = query_trade_signals(1, direction='buy', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals['pos_id'].values[0], 1)
        self.assertEqual(signals['direction'].values[0], 'buy')
        self.assertEqual(signals['qty'].values[0], 300)
        self.assertEqual(signals['price'].values[0], 10.0)
        self.assertEqual(signals['status'].values[0], 'created')
        self.assertEqual(signals['pos_id'].values[1], 3)
        self.assertEqual(signals['direction'].values[1], 'buy')
        self.assertEqual(signals['qty'].values[1], 500)
        self.assertEqual(signals['price'].values[1], 20.0)
        self.assertEqual(signals['status'].values[1], 'canceled')

        # test query signals with bad input
        signals = query_trade_signals(1, symbol='AAPL', position='long', status='filled', data_source=self.test_ds)
        self.assertIsNone(signals)
        signals = query_trade_signals(1, symbol='invalid', position='long', status='filled', data_source=self.test_ds)
        self.assertIsNone(signals)
        signals = query_trade_signals(1, symbol='GOOG', position='invalid', status='filled', data_source=self.test_ds)
        self.assertIsNone(signals)
        signals = query_trade_signals(1, symbol='GOOG', position='long', status='invalid', data_source=self.test_ds)
        self.assertIsNone(signals)
        signals = query_trade_signals(1, symbol='GOOG', position='long', direction='invalid', data_source=self.test_ds)
        self.assertIsNone(signals)
        signals = query_trade_signals(999, symbol='GOOG', position='long', direction='buy', data_source=self.test_ds)
        self.assertIsNone(signals)
        signals = query_trade_signals(1, symbol=123, position='long', direction='buy', data_source=self.test_ds)
        self.assertIsNone(signals)
        signals = query_trade_signals(1, symbol='GOOG', position=123, direction='buy', data_source=self.test_ds)
        self.assertIsNone(signals)
        signals = query_trade_signals(1, symbol='GOOG', position='long', direction=123, data_source=self.test_ds)
        self.assertIsNone(signals)

    # test 2nd foundational functions: save_parsed_signals / submit_signal / output_trade_signal
    def test_save_parsed_signals(self):
        """ test save_parsed_signals function """
        # remove all data in test datasource
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        if self.test_ds.table_data_exists('sys_op_trade_signals'):
            self.test_ds.drop_table_data('sys_op_trade_signals')
        # create test accounts, positions should be created automatically with signals
        new_account('test_user1', 100000, self.test_ds)
        new_account('test_user2', 150000, self.test_ds)
        # create test signals with parsed signals, which include list of symbols, positions, directions, qty, and prices
        # parsed signals has 5 symbols, with only long position, and buy direction
        parsed_signals = (
            ['GOOG', 'FB', 'AAPL', 'AMZN', 'MSFT'],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'buy', 'buy', 'buy', 'buy'],
            [100, 200, 300, 400, 500],
            [10.0, 20.0, 30.0, 40.0, 50.0]
        )
        # save parsed signals
        signal_ids = save_parsed_trade_signals(
                account_id=1,
                symbols=parsed_signals[0],
                positions=parsed_signals[1],
                directions=parsed_signals[2],
                quantities=parsed_signals[3],
                prices=parsed_signals[4],
                data_source=self.test_ds
        )
        # query signals from database
        self.assertEqual(len(signal_ids), 5)
        signal_detail = read_trade_signal_detail(signal_ids[0], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 1)
        self.assertEqual(signal_detail['symbol'], 'GOOG')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 100)
        self.assertEqual(signal_detail['price'], 10.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_signal_detail(signal_ids[1], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 2)
        self.assertEqual(signal_detail['symbol'], 'FB')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 200)
        self.assertEqual(signal_detail['price'], 20.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_signal_detail(signal_ids[2], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 3)
        self.assertEqual(signal_detail['symbol'], 'AAPL')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 300)
        self.assertEqual(signal_detail['price'], 30.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_signal_detail(signal_ids[3], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 4)
        self.assertEqual(signal_detail['symbol'], 'AMZN')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 400)
        self.assertEqual(signal_detail['price'], 40.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_signal_detail(signal_ids[4], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 5)
        self.assertEqual(signal_detail['symbol'], 'MSFT')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 500)
        self.assertEqual(signal_detail['price'], 50.0)
        self.assertEqual(signal_detail['status'], 'created')
        # create test positions for account 2, and add buy and sell signals for account 2
        get_or_create_position(2, 'GOOG', 'long', self.test_ds)  # pos_id = 6, qty = 1000
        get_or_create_position(2, 'FB', 'long', self.test_ds)  # pos_id = 7
        get_or_create_position(2, 'AAPL', 'long', self.test_ds)  # pos_id = 8
        get_or_create_position(2, 'AMZN', 'long', self.test_ds)   # pos_id = 9
        get_or_create_position(2, 'MSFT', 'long', self.test_ds)  # pos_id = 10
        get_or_create_position(2, 'GOOG', 'short', self.test_ds)  # pos_id = 11
        get_or_create_position(2, 'FB', 'short', self.test_ds)  # pos_id = 12
        get_or_create_position(2, 'AAPL', 'short', self.test_ds)  # pos_id = 13
        get_or_create_position(2, 'AMZN', 'short', self.test_ds)  # pos_id = 14
        get_or_create_position(2, 'MSFT', 'short', self.test_ds)  # pos_id = 15
        # set position qty 1000 for some positions, make sure that only
        # either long or short position qty is 1000 for each symbol
        update_position(6, self.test_ds, qty_change=1000, available_qty_change=1000)
        update_position(8, self.test_ds, qty_change=1000, available_qty_change=1000)
        update_position(12, self.test_ds, qty_change=1000, available_qty_change=1000)
        update_position(14, self.test_ds, qty_change=1000, available_qty_change=1000)
        update_position(10, self.test_ds, qty_change=1000, available_qty_change=1000)
        # create test signals for account 2, apply sell signals on positions with qty 1000
        parsed_signals = (
            ['GOOG', 'FB', 'AAPL', 'AMZN', 'MSFT'],
            ['long', 'long', 'short', 'short', 'long'],
            ['sell', 'buy', 'buy', 'sell', 'sell'],
            [100, 200, 300, 400, 500],
            [10.0, 20.0, 30.0, 40.0, 50.0]
        )
        signal_ids = save_parsed_trade_signals(
                account_id=2,
                symbols=parsed_signals[0],
                positions=parsed_signals[1],
                directions=parsed_signals[2],
                quantities=parsed_signals[3],
                prices=parsed_signals[4],
                data_source=self.test_ds
        )
        # check signal detail
        self.assertEqual(len(signal_ids), 5)
        signal_detail = read_trade_signal_detail(signal_ids[0], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 6)
        self.assertEqual(signal_detail['symbol'], 'GOOG')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'sell')
        self.assertEqual(signal_detail['qty'], 100)
        self.assertEqual(signal_detail['price'], 10.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_signal_detail(signal_ids[1], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 7)
        self.assertEqual(signal_detail['symbol'], 'FB')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 200)
        self.assertEqual(signal_detail['price'], 20.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_signal_detail(signal_ids[2], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 13)
        self.assertEqual(signal_detail['symbol'], 'AAPL')
        self.assertEqual(signal_detail['position'], 'short')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 300)
        self.assertEqual(signal_detail['price'], 30.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_signal_detail(signal_ids[3], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 14)
        self.assertEqual(signal_detail['symbol'], 'AMZN')
        self.assertEqual(signal_detail['position'], 'short')
        self.assertEqual(signal_detail['direction'], 'sell')
        self.assertEqual(signal_detail['qty'], 400)
        self.assertEqual(signal_detail['price'], 40.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_signal_detail(signal_ids[4], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 10)
        self.assertEqual(signal_detail['symbol'], 'MSFT')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'sell')
        self.assertEqual(signal_detail['qty'], 500)
        self.assertEqual(signal_detail['price'], 50.0)
        self.assertEqual(signal_detail['status'], 'created')
        # check position detail

    def test_submit_signal(self):
        """ test submit_signal function """
        # remove all data in test datasource
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        if self.test_ds.table_data_exists('sys_op_trade_signals'):
            self.test_ds.drop_table_data('sys_op_trade_signals')
        # create test data, including two test accounts, 10 test positions, 5 for each account
        # create test accounts
        new_account('test_user1', 100000, self.test_ds)
        new_account('test_user2', 150000, self.test_ds)
        # create test positions
        get_or_create_position(1, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'MSFT', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'AMZN', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'FB', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'MSFT', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'AMZN', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'FB', 'long', data_source=self.test_ds)
        # set up position quantities and available amounts
        update_position(1, data_source=self.test_ds, qty_change=100, available_qty_change=100)
        update_position(2, data_source=self.test_ds, qty_change=200, available_qty_change=200)
        update_position(3, data_source=self.test_ds, qty_change=300, available_qty_change=300)
        update_position(4, data_source=self.test_ds, qty_change=400, available_qty_change=400)
        update_position(5, data_source=self.test_ds, qty_change=500, available_qty_change=500)
        update_position(6, data_source=self.test_ds, qty_change=600, available_qty_change=600)
        update_position(7, data_source=self.test_ds, qty_change=700, available_qty_change=700)
        update_position(8, data_source=self.test_ds, qty_change=800, available_qty_change=800)
        update_position(9, data_source=self.test_ds, qty_change=900, available_qty_change=900)
        update_position(10, data_source=self.test_ds, qty_change=1000, available_qty_change=1000)
        # print out position data of both accounts
        print(f'position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}')
        print(f'position data of account_id == 2: \n'
              f'{get_account_positions(2, data_source=self.test_ds)}')

        # create test signals, 10 signals in total, quantity does not exceed available amount
        parsed_signals_batch_1 = (
            ['GOOG', 'AAPL', 'MSFT', 'AMZN', 'FB', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'sell', 'sell', 'buy', 'buy'],
            [100, 100, 300, 400, 500],
            [60.0, 70.0, 80.0, 90.0, 100.0],
        )
        # save first batch of signals
        signal_ids = save_parsed_trade_signals(
                account_id=1,
                symbols=parsed_signals_batch_1[0],
                positions=parsed_signals_batch_1[1],
                directions=parsed_signals_batch_1[2],
                quantities=parsed_signals_batch_1[3],
                prices=parsed_signals_batch_1[4],
                data_source=self.test_ds,
        )
        print('signal ids of first batch: {}'.format(signal_ids))
        print(f'before submission, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        # submit first batch of signals one by one
        submit_signal(1, data_source=self.test_ds)
        print(f'after submitting signal 1, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty']
        aqty = position['available_qty']
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_signal(2, data_source=self.test_ds)
        print(f'after submitting signal 2, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 100, 300, 400, 500]))

        submit_signal(3, data_source=self.test_ds)
        print(f'after submitting signal 3, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 100, 0, 400, 500]))

        submit_signal(4, data_source=self.test_ds)
        print(f'after submitting signal 4, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60 - 400 * 90)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 100, 0, 400, 500]))

        submit_signal(5, data_source=self.test_ds)
        print(f'after submitting signal 5, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60 - 400 * 90 - 500 * 100)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 100, 0, 400, 500]))

        # check status of all signals
        signal_detail = read_trade_signal_detail(1, data_source=self.test_ds)
        print(f'signal_detail of signal 1: {signal_detail}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        self.assertEqual(signal_detail['status'], 'submitted')
        self.assertIsInstance(signal_detail['submitted_time'], str)

        # create second batch of signals, quantity exceeds available amount
        parsed_signals_batch_2 = (
            ['GOOG', 'AAPL', 'MSFT', 'AMZN', 'FB'],
            ['long', 'long', 'long', 'long', 'long'],
            ['sell', 'sell', 'sell', 'buy', 'buy'],
            [100, 700, 800, 900, 1000],
            [10.0, 20.0, 30.0, 40.0, 50.0],
        )
        # save second batch of signals
        signal_ids = save_parsed_trade_signals(
                account_id=1,
                symbols=parsed_signals_batch_2[0],
                positions=parsed_signals_batch_2[1],
                directions=parsed_signals_batch_2[2],
                quantities=parsed_signals_batch_2[3],
                prices=parsed_signals_batch_2[4],
                data_source=self.test_ds,
        )
        print('signal ids of second batch: {}'.format(signal_ids))
        print(f'before submission, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}')
        # submit second batch of signals one by one
        submit_signal(6, data_source=self.test_ds)
        print(f'after submitting signal 6, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60 - 400 * 90 - 500 * 100)
        signal = read_trade_signal_detail(6, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 100)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [0, 100, 0, 400, 500]))

        submit_signal(7, data_source=self.test_ds)  # 此时需要卖出700股，但只有100股可用
        print(f'after submitting signal 7, position data of account_id == 1: \n'
                f'{get_account_positions(1, data_source=self.test_ds)}\n'
                f'cash availability of account_id == 1: \n'
                f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60 - 400 * 90 - 500 * 100)
        signal = read_trade_signal_detail(7, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 100)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [0, 0, 0, 400, 500]))

        submit_signal(8, data_source=self.test_ds)  # 此时需要卖出800股，但已经没有可用股份
        print(f'after submitting signal 8, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60 - 400 * 90 - 500 * 100)
        signal = read_trade_signal_detail(8, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 0)  # TODO, quantity is 0, 是否应该允许这种情况？
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [0, 0, 0, 400, 500]))

        submit_signal(9, data_source=self.test_ds)  # 此时需要买入900股，但可用现金仅够买入200股
        print(f'after submitting signal 9, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60 - 400 * 90 - 500 * 100 - 200 * 40)
        signal = read_trade_signal_detail(9, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 200)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [0, 0, 0, 400, 500]))

        submit_signal(10, data_source=self.test_ds)  # 此时已经没有可用现金
        print(f'after submitting signal 10, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000 - 100 * 60 - 400 * 90 - 500 * 100 - 200 * 40)
        signal = read_trade_signal_detail(10, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 0)  # TODO, quantity is 0, 是否应该允许这种情况？
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [0, 0, 0, 400, 500]))

    def test_output_signal(self):
        """ test output_trade_signal function """
        pass

    def test_read_and_write_result(self):
        """ test read_trade_result and write_trade_result functions """
        # 检查datasource中的数据表，删除所有的trade_result数据
        if self.test_ds.table_data_exists('sys_op_trade_results'):
            self.test_ds.drop_table_data('sys_op_trade_results')
        # 生成一个trade_result
        trade_result = {
            'signal_id': 1,
            'filled_qty': 100.0,
            'price': 10.0,
            'transaction_fee': 5.0,
            'execution_time': pd.to_datetime('now'),
            'canceled_qty': 0.0,
        }
        # 将trade_result写入datasource
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        # 从datasource中读取trade_result
        trade_result = read_trade_result_by_id(result_id, data_source=self.test_ds)
        # 检查读取的trade_result是否与写入的trade_result一致
        self.assertIsInstance(trade_result, dict)
        self.assertEqual(trade_result['signal_id'], 1)
        self.assertEqual(trade_result['filled_qty'], 100.0)
        self.assertEqual(trade_result['price'], 10.0)
        self.assertEqual(trade_result['transaction_fee'], 5.0)
        self.assertEqual(trade_result['canceled_qty'], 0.0)
        # 再次写入两个trade_results，signal_id分别为1, 2，检查是否能正确读取signal_id为1的两条交易结果
        trade_result = {
            'signal_id': 1,
            'filled_qty': 200.0,
            'price': 10.5,
            'transaction_fee': 5.0,
            'execution_time': pd.to_datetime('now'),
            'canceled_qty': 0.0,
        }
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        self.assertEqual(result_id, 2)
        trade_result = {
            'signal_id': 2,
            'filled_qty': 0.0,
            'price': 10.0,
            'transaction_fee': 5.0,
            'execution_time': pd.to_datetime('now'),
            'canceled_qty': 100.0,
        }
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        self.assertEqual(result_id, 3)
        trade_results = read_trade_results_by_signal_id(signal_id=1, data_source=self.test_ds)
        self.assertIsInstance(trade_results, pd.DataFrame)
        self.assertEqual(len(trade_results), 2)
        self.assertEqual(trade_results['signal_id'].loc[1], 1)
        self.assertEqual(trade_results['signal_id'].loc[2], 1)
        self.assertEqual(trade_results['filled_qty'].loc[1], 100.0)
        self.assertEqual(trade_results['filled_qty'].loc[2], 200.0)
        self.assertEqual(trade_results['price'].loc[1], 10.0)
        self.assertEqual(trade_results['price'].loc[2], 10.5)
        self.assertEqual(trade_results['transaction_fee'].loc[1], 5.0)
        self.assertEqual(trade_results['transaction_fee'].loc[2], 5.0)
        self.assertEqual(trade_results['canceled_qty'].loc[1], 0.0)
        self.assertEqual(trade_results['canceled_qty'].loc[2], 0.0)

        # test write_trade_result with bad input
        with self.assertRaises(TypeError):
            write_trade_result(None, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'signal_id': '1',
                'filled_qty': 200.0,
                'price': 10.5,
                'transaction_fee': 5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': '200.0',
                'price': 10.5,
                'transaction_fee': 5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': 200.0,
                'price': '10.5',
                'transaction_fee': 5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': 200.0,
                'price': 10.5,
                'transaction_fee': '5.0',
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': 200.0,
                'price': 10.5,
                'transaction_fee': 5.0,
                'execution_time': 'now',
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': 200.0,
                'price': 10.5,
                'transaction_fee': 5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': '0.0',
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'signal_id': -1,
                'filled_qty': 200.0,
                'price': 10.5,
                'transaction_fee': 5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': -200.0,
                'price': 10.5,
                'transaction_fee': 5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': 200.0,
                'price': -10.5,
                'transaction_fee': 5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': 200.0,
                'price': 10.5,
                'transaction_fee': -5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': 0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'signal_id': 1,
                'filled_qty': 200.0,
                'price': 10.5,
                'transaction_fee': 5.0,
                'execution_time': pd.to_datetime('now'),
                'canceled_qty': -100.0,
            }, data_source=self.test_ds)

    def test_process_trade_signals(self):
        """ test full process of trade signal generation, submission and result recording"""
        # 检查datasource中的数据表，删除所有的account, positions, trade_signal, trade_result数据
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        if self.test_ds.table_data_exists('sys_op_trade_signals'):
            self.test_ds.drop_table_data('sys_op_trade_signals')
        if self.test_ds.table_data_exists('sys_op_trade_results'):
            self.test_ds.drop_table_data('sys_op_trade_results')
        # 重新创建account及trade_signal数据, position会在submit_signal中自动创建
        # create test accounts
        new_account('test_user1', 100000, self.test_ds)
        # create test trade signals
        # create test signals, all signals are buy signals, because the test starts with zero positions
        parsed_signals_batch_1 = (
            ['GOOG', 'AAPL', 'MSFT', 'AMZN', 'FB', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'buy', 'buy', 'buy', 'buy'],
            [100, 100, 300, 400, 500],
            [60.0, 70.0, 80.0, 90.0, 30.0],
        )
        # save first batch of signals
        signal_ids = save_parsed_trade_signals(
                account_id=1,
                symbols=parsed_signals_batch_1[0],
                positions=parsed_signals_batch_1[1],
                directions=parsed_signals_batch_1[2],
                quantities=parsed_signals_batch_1[3],
                prices=parsed_signals_batch_1[4],
                data_source=self.test_ds,
        )
        self.assertEqual(signal_ids, [1, 2, 3, 4, 5])
        # 逐个提交交易信号并打印相关余额的变化
        submit_signal(1, data_source=self.test_ds)
        print(f'after submitting signal 1, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        submit_signal(2, data_source=self.test_ds)
        print(f'after submitting signal 2, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        submit_signal(3, data_source=self.test_ds)
        print(f'after submitting signal 3, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        submit_signal(4, data_source=self.test_ds)
        print(f'after submitting signal 4, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        submit_signal(5, data_source=self.test_ds)
        print(f'after submitting signal 5, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        # 生成交易结果并逐个处理, 注意raw_results没有execution_time字段
        raw_trade_result = {
            'signal_id': 1,
            'filled_qty': 100,
            'price': 60.0,
            'transaction_fee': 5.0,
            'canceled_qty': 0.0,
        }

        raise NotImplementedError

    # test top level functions related to signal generation and submission
    def test_parse_signal(self):
        """ test parse_trade_signal function """
        # test parse_trade_signal with three symbols, with three signal types
        # create basic test data
        shares = ['000001', '000002', '000003']
        prices = np.array([20., 20., 20.])
        own_shares = np.array([500., 500., 1000.])
        own_cash = 100000.0
        available_amounts = np.array([500., 500., 1000.])
        available_cash = 100000.0
        test_config = {
            'pt_buy_threshold': 0.0,
            'pt_sell_threshold': 0.0,
            'allow_sell_short': True,
        }
        # create test data for PT signal and parse it
        pt_signal = np.array([0.1, 0.1, 0.1])
        parsed_signal_elements = parse_trade_signal(
            signals=pt_signal,
            signal_type='pt',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with signal {pt_signal}: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['buy', 'buy', 'sell'])
        self.assertEqual(parsed_signal_elements[3], [200.0, 200.0, 300.0])
        pt_signal = np.array([-0.1, 0.2, 0.3])
        parsed_signal_elements = parse_trade_signal(
            signals=pt_signal,
            signal_type='pt',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with signal {pt_signal}: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'short', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['sell', 'buy', 'buy', 'buy'])
        self.assertEqual(parsed_signal_elements[3], [500.0, 700.0, 900.0, 1100.0])

        # create test data for PS signal and parse it
        ps_signal = np.array([0.1, 0.1, 0.1])
        parsed_signal_elements = parse_trade_signal(
            signals=ps_signal,
            signal_type='ps',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with ps signal {ps_signal}: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['buy', 'buy', 'buy'])
        self.assertEqual(parsed_signal_elements[3], [700.0, 700.0, 700.0])
        ps_signal = np.array([-1.5, -1, 0.3])
        parsed_signal_elements = parse_trade_signal(
            signals=ps_signal,
            signal_type='ps',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with ps signal {ps_signal}: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'short', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['sell', 'buy', 'sell', 'buy'])
        self.assertEqual(parsed_signal_elements[3], [500.0, 250.0, 500.0, 2100.0])

        # create test data for VS signal and parse it
        vs_signal = np.array([300, 400, 500])
        parsed_signal_elements = parse_trade_signal(
            signals=vs_signal,
            signal_type='vs',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with vs signal {vs_signal}: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['buy', 'buy', 'buy'])
        self.assertEqual(parsed_signal_elements[3], [300.0, 400.0, 500.0])
        vs_signal = np.array([-1300, 400, -500])
        parsed_signal_elements = parse_trade_signal(
            signals=vs_signal,
            signal_type='vs',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with vs signal {vs_signal}: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'short', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['sell', 'buy', 'buy', 'sell'])
        self.assertEqual(parsed_signal_elements[3], [500.0, 800.0, 400.0, 500.0])

        # test allow_sell_short = False
        test_config = {
            'pt_buy_threshold': 0.1,
            'pt_sell_threshold': -0.1,
            'allow_sell_short': False,
        }
        # test pt signal previously used
        pt_signal = np.array([-0.1, 0.2, 0.3])
        parsed_signal_elements = parse_trade_signal(
            signals=pt_signal,
            signal_type='pt',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with signal {pt_signal} not allow short: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['sell', 'buy', 'buy'])
        self.assertEqual(parsed_signal_elements[3], [500.0, 900.0, 1100.0])
        # test ps signal previously used
        ps_signal = np.array([-1.5, -1, 0.3])
        parsed_signal_elements = parse_trade_signal(
            signals=ps_signal,
            signal_type='ps',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with signal {ps_signal} not allow short: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['sell', 'sell', 'buy'])
        self.assertEqual(parsed_signal_elements[3], [500.0, 500.0, 2100.0])
        # test vs signal previously used
        vs_signal = np.array([-1300, 400, -500])
        parsed_signal_elements = parse_trade_signal(
            signals=vs_signal,
            signal_type='vs',
            shares=shares,
            prices=prices,
            own_amounts=own_shares,
            own_cash=own_cash,
            available_amounts=available_amounts,
            available_cash=available_cash,
            config=test_config,
        )
        print(f'parsed_signal_elements with vs signal {vs_signal} not allow short: \n{parsed_signal_elements}')
        self.assertEqual(parsed_signal_elements[0], ['000001', '000002', '000003'])
        self.assertEqual(parsed_signal_elements[1], ['long', 'long', 'long'])
        self.assertEqual(parsed_signal_elements[2], ['sell', 'buy', 'sell'])
        self.assertEqual(parsed_signal_elements[3], [500.0, 400.0, 500.0])

        # TODO: test parse_trade_signal with different config:
        #  1. vs type of signals done
        #  2, allow_sell_short = False done
        #  3. no available cash and no available shares

    def test_itemize_trade_signals(self):
        """ test itemize trade signals"""
        # test itemize_trade_signals with only one symbol, buy 500 shares in long position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([5000.0])
        amounts_to_sell = np.array([0.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
        )
        self.assertEqual(symbols, ['000001'])
        self.assertEqual(positions, ['long'])
        self.assertEqual(directions, ['buy'])
        self.assertEqual(quantities, [500.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0])

        # test itemize_trade_signals with only one symbol, sell 500 shares in long position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([-500.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
        )
        self.assertEqual(symbols, ['000001'])
        self.assertEqual(positions, ['long'])
        self.assertEqual(directions, ['sell'])
        self.assertEqual(quantities, [500.0])

        # test itemize_trade_signals with only one symbol, sell 500 shares in short position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([500.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
                allow_sell_short=True,
        )
        self.assertEqual(symbols, ['000001'])
        self.assertEqual(positions, ['short'])
        self.assertEqual(directions, ['sell'])
        self.assertEqual(quantities, [500.0])

        # test itemize_trade_signals with only one symbol, buy 500 shares in short position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([-5000.0])
        amounts_to_sell = np.array([0.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
                allow_sell_short=True,
        )
        self.assertEqual(symbols, ['000001'])
        self.assertEqual(positions, ['short'])
        self.assertEqual(directions, ['buy'])
        self.assertEqual(quantities, [500.0])

        # test itemize_trade_signals with only one symbol, sell 1000 shares while only 500 shares available
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([-1000.0])
        available_cash = 10000.0
        available_amounts = np.array([700.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
                allow_sell_short=True,
        )
        self.assertEqual(symbols, ['000001', '000001'])
        self.assertEqual(positions, ['long', 'short'])
        self.assertEqual(directions, ['sell', 'buy'])
        self.assertEqual(quantities, [700.0, 300.0])

        # test itemize_trade_signals with only one symbol, sell 1000 short shares while only 500 short shares available
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([1000.0])
        available_cash = 10000.0
        available_amounts = np.array([-700.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
                allow_sell_short=True,
        )
        self.assertEqual(symbols, ['000001', '000001'])
        self.assertEqual(positions, ['short', 'long'])
        self.assertEqual(directions, ['sell', 'buy'])
        self.assertEqual(quantities, [700.0, 300.0])

        # test itemize_trade_signals with only one symbol, buy shares with not enough cash
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([10000.0])
        amounts_to_sell = np.array([0.0])
        available_cash = 5000.0
        available_amounts = np.array([1000.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
        )
        self.assertEqual(symbols, ['000001'])
        self.assertEqual(positions, ['long'])
        self.assertEqual(directions, ['buy'])
        self.assertEqual(quantities, [500.0])

        # test itemize_trade_signals with multiple symbols
        shares = ['000001', '000002', '000003', '000004', '000005', '000006']
        prices = np.array([10., 10., 10., 10., 10., 10.])
        cash_to_spend = np.array([5000.0, 0.0, 0.0, 3500.0, -1000.0, 0.0])
        amounts_to_sell = np.array([0.0, 0.0, 500.0, 150.0, 0.0, 500.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
                allow_sell_short=True,
        )
        self.assertEqual(symbols, ['000001', '000003', '000004', '000004', '000005', '000006'])
        self.assertEqual(positions, ['long', 'short', 'long', 'short', 'short', 'short'])
        self.assertEqual(directions, ['buy', 'sell', 'buy', 'sell', 'buy', 'sell'])
        self.assertEqual(quantities, [500.0, 500.0, 350.0, 150.0, 100.0, 500.0])

        # test itemize_trade_signals with multiple symbols, with a few sell amounts exceeding available amounts

    def test_parse_pt_signals(self):
        """ test parsing trade signal from pt_type signal"""
        # test parsing pt buy long signal with only one symbol
        signals = np.array([1])
        prices = np.array([10.])
        own_amounts = np.array([0.0])
        own_cash = 5000.0
        pt_buy_threshold = 0.5
        pt_sell_threshold = 0.5

        cash_to_spend, amounts_to_sell = parse_pt_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                pt_buy_threshold=pt_buy_threshold,
                pt_sell_threshold=pt_sell_threshold,
                allow_sell_short=False
        )
        self.assertEqual(cash_to_spend, [5000.0])
        self.assertEqual(amounts_to_sell, [0.0])

        # test parsing pt sell long signal with only one symbol
        signals = np.array([0])
        prices = np.array([10.])
        own_amounts = np.array([500.0])
        own_cash = 0.0
        pt_buy_threshold = 0.5
        pt_sell_threshold = 0.5

        cash_to_spend, amounts_to_sell = parse_pt_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                pt_buy_threshold=pt_buy_threshold,
                pt_sell_threshold=pt_sell_threshold,
                allow_sell_short=False
        )
        self.assertEqual(cash_to_spend, [0.0])
        self.assertEqual(amounts_to_sell, [-500.0])

        # test parsing pt buy short signal with only one symbol
        signals = np.array([-1])
        prices = np.array([10.])
        own_amounts = np.array([0.0])
        own_cash = 5000.0
        pt_buy_threshold = 0.5
        pt_sell_threshold = 0.5

        cash_to_spend, amounts_to_sell = parse_pt_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                pt_buy_threshold=pt_buy_threshold,
                pt_sell_threshold=pt_sell_threshold,
                allow_sell_short=True
        )
        self.assertEqual(cash_to_spend, [-5000.0])
        self.assertEqual(amounts_to_sell, [0.0])

        # test parsing pt sell short signal with only one symbol
        signals = np.array([0])
        prices = np.array([10.])
        own_amounts = np.array([-500.0])
        own_cash = 10000.0
        pt_buy_threshold = 0.5
        pt_sell_threshold = 0.5

        cash_to_spend, amounts_to_sell = parse_pt_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                pt_buy_threshold=pt_buy_threshold,
                pt_sell_threshold=pt_sell_threshold,
                allow_sell_short=True
        )
        self.assertEqual(cash_to_spend, [0.0])
        self.assertEqual(amounts_to_sell, [500.0])

        # test parsing pt multi-type signal with multiple symbols

        signals = np.array([0, 0.2, 0, 0.1, -0.2, -0.3])
        prices = np.array([10., 10., 10., 10., 10., 10.])
        own_amounts = np.array([0.0, 0.0, 500.0, 150.0, 0.0, -500.0])
        own_cash = 10000.0
        pt_buy_threshold = 0.1
        pt_sell_threshold = 0.1

        cash_to_spend, amounts_to_sell = parse_pt_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                pt_buy_threshold=pt_buy_threshold,
                pt_sell_threshold=pt_sell_threshold,
                allow_sell_short=True
        )
        self.assertEqual(list(cash_to_spend), [0.0, 2300.0, 0.0, 0.0, -2300.0, 0.0])
        self.assertEqual(list(amounts_to_sell), [0.0, 0.0, -500.0, 0.0, 0.0, 155.0])

    def test_parse_ps_signals(self):
        """ test parse_ps_signals function """
        # test parsing ps buy long signal with only one symbol
        signals = np.array([1])
        prices = np.array([10.])
        own_amounts = np.array([0.0])
        own_cash = 5000.0

        cash_to_spend, amounts_to_sell = parse_ps_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                allow_sell_short=False
        )
        self.assertEqual(cash_to_spend, [5000.0])
        self.assertEqual(amounts_to_sell, [0.0])

        # test parsing ps sell long signal with only one symbol
        signals = np.array([-1])
        prices = np.array([10.])
        own_amounts = np.array([500.0])
        own_cash = 0.0

        cash_to_spend, amounts_to_sell = parse_ps_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                allow_sell_short=False
        )
        self.assertEqual(cash_to_spend, [0.0])
        self.assertEqual(amounts_to_sell, [-500.0])

        # test parsing ps buy short signal with only one symbol
        signals = np.array([-1])
        prices = np.array([10.])
        own_amounts = np.array([0.0])
        own_cash = 5000.0

        cash_to_spend, amounts_to_sell = parse_ps_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                allow_sell_short=True
        )
        self.assertEqual(cash_to_spend, [-5000.0])
        self.assertEqual(amounts_to_sell, [0.0])

        # test parsing ps sell short signal with only one symbol
        signals = np.array([1])
        prices = np.array([10.])
        own_amounts = np.array([-500.0])
        own_cash = 0.0

        cash_to_spend, amounts_to_sell = parse_ps_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                allow_sell_short=True
        )
        self.assertEqual(cash_to_spend, [0.0])
        self.assertEqual(amounts_to_sell, [500.0])

        # test parsing ps multi-type signal with multiple symbols

        signals = np.array([1, 0, -1, 0, -1, 0.5])
        prices = np.array([10., 10., 10., 10., 10., 10.])
        own_amounts = np.array([0.0, 0.0, 500.0, 150.0, 0.0, -500.0])
        own_cash = 0.0

        cash_to_spend, amounts_to_sell = parse_ps_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                allow_sell_short=True
        )
        self.assertEqual(list(cash_to_spend), [1500.0, 0.0, 0.0, 0.0, -1500.0, 0.0])
        self.assertEqual(list(amounts_to_sell), [0.0, 0.0, -500.0, 0.0, 0.0, 250.0])

    def test_parse_vs_signals(self):
        """ test parse_vs_signals function """
        # test parsing vs buy long signal with only one symbol
        signals = np.array([500])
        prices = np.array([10.])
        own_amounts = np.array([0.0])

        cash_to_spend, amounts_to_sell = parse_vs_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                allow_sell_short=False
        )
        self.assertEqual(cash_to_spend, [5000.0])
        self.assertEqual(amounts_to_sell, [0.0])

        # test parsing vs sell long signal with only one symbol
        signals = np.array([-500])
        prices = np.array([10.])
        own_amounts = np.array([500.0])

        cash_to_spend, amounts_to_sell = parse_vs_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                allow_sell_short=False
        )
        self.assertEqual(cash_to_spend, [0.0])
        self.assertEqual(amounts_to_sell, [-500.0])

        # test parsing vs buy short signal with only one symbol
        signals = np.array([-500])
        prices = np.array([10.])
        own_amounts = np.array([0.0])

        cash_to_spend, amounts_to_sell = parse_vs_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                allow_sell_short=True
        )
        self.assertEqual(cash_to_spend, [-5000.0])
        self.assertEqual(amounts_to_sell, [0.0])

        # test parsing vs sell short signal with only one symbol
        signals = np.array([500])
        prices = np.array([10.])
        own_amounts = np.array([-500.0])

        cash_to_spend, amounts_to_sell = parse_vs_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                allow_sell_short=True
        )
        self.assertEqual(cash_to_spend, [0.0])
        self.assertEqual(amounts_to_sell, [500.0])

        # test parsing vs multi-type signal with multiple symbols

        signals = np.array([500, 0, -500, -250, 0, 250])
        prices = np.array([10., 10., 10., 10., 10., 10.])
        own_amounts = np.array([0.0, 0.0, 500.0, -250.0, 0.0, -500.0])

        cash_to_spend, amounts_to_sell = parse_vs_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                allow_sell_short=True
        )
        self.assertEqual(list(cash_to_spend), [5000.0, 0.0, 0.0, -2500.0, 0.0, 0.0])
        self.assertEqual(list(amounts_to_sell), [0.0, 0.0, -500.0, 0.0, 0.0, 250.0])


if __name__ == '__main__':
    unittest.main()
