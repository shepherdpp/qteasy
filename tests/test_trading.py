# coding=utf-8
# ======================================
# File:     test_trading.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-02-20
# Desc:
#   Unittest for functions related to
# live trade, including trade data
# recording and utility functions
# ======================================

import unittest

import qteasy as qt
import pandas as pd
import numpy as np

from qteasy.database import DataSource

from qteasy.trading_util import _parse_pt_signals, _parse_ps_signals, _parse_vs_signals, _signal_to_order_elements
from qteasy.trading_util import parse_trade_signal, submit_order, get_last_trade_result_summary, get_symbol_names
from qteasy.trading_util import process_trade_result, process_account_delivery, create_daily_task_schedule
from qteasy.trading_util import calculate_cost_change

from qteasy.trade_recording import new_account, get_account, update_account, update_account_balance
from qteasy.trade_recording import update_position, get_account_positions, get_or_create_position
from qteasy.trade_recording import record_trade_order, update_trade_order, read_trade_order
from qteasy.trade_recording import query_trade_orders, get_position_by_id, update_trade_result
from qteasy.trade_recording import get_position_ids, read_trade_order_detail, save_parsed_trade_orders
from qteasy.trade_recording import get_account_cash_availabilities, get_account_position_availabilities
from qteasy.trade_recording import write_trade_result, get_account_position_details, read_trade_result_by_id
from qteasy.trade_recording import read_trade_results_by_order_id, delete_account


class TestTradeRecording(unittest.TestCase):

    def setUp(self) -> None:
        """ execute before each test"""
        from qteasy import QT_ROOT_PATH, QT_CONFIG
        self.qt_root_path = QT_ROOT_PATH
        self.data_test_dir = '../qteasy/data_test/'
        # 创建一个专用的测试数据源，以免与已有的文件混淆，不需要测试所有的数据源，因为相关测试在test_datasource中已经完成
        # self.test_ds = DataSource('file', file_type='hdf', file_loc=self.data_test_dir)
        self.test_ds = DataSource(
                'db',
                host=QT_CONFIG['test_db_host'],
                port=QT_CONFIG['test_db_port'],
                user=QT_CONFIG['test_db_user'],
                password=QT_CONFIG['test_db_password'],
                db_name=QT_CONFIG['test_db_name'],
                allow_drop_table=True,
        )
        # 清空测试数据源中的所有相关表格数据
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
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
        account_id = new_account(user_name=user_name, cash_amount=cash_amount, data_source=self.test_ds)
        print(f'account created, id: {account_id}')
        self.assertEqual(account_id, 1)
        # add two more accounts
        new_account(user_name='test_user2', cash_amount=20000, data_source=self.test_ds)
        new_account(user_name='test_user3', cash_amount=30000, data_source=self.test_ds)
        # test get_account
        account = get_account(2, data_source=self.test_ds)
        self.assertEqual(account['user_name'], 'test_user2')
        self.assertEqual(account['cash_amount'], 20000.0)
        self.assertEqual(account['available_cash'], 20000.0)
        # test add account with negative cash amount
        with self.assertRaises(ValueError):
            new_account(user_name='test_user4', cash_amount=-10000, data_source=self.test_ds)
        # test get account with non-existing account id
        with self.assertRaises(KeyError):
            get_account(4, data_source=self.test_ds)

    def test_update_account(self):
        """ test update_account function """
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        # read all accounts from datasource and modify the username
        new_account(user_name='test_user', cash_amount=10000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=20000, data_source=self.test_ds)
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
        new_account(user_name='test_user', cash_amount=10000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=20000, data_source=self.test_ds)
        pos_id = get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 1)
        pos_id = get_or_create_position(1, 'APPL', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 2)
        pos_id = get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        print(position)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'APPL')
        self.assertEqual(position['position'], 'long')
        self.assertEqual(position['qty'], 0)
        pos_id = get_or_create_position(1, 'APPL', 'short', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'APPL')
        self.assertEqual(position['position'], 'short')
        self.assertEqual(position['qty'], 0)
        # add more positions to account 2
        get_or_create_position(2, 'APPL', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'APPL', 'short', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'short', data_source=self.test_ds)
        # test get_or_create_position with non-existing account id
        with self.assertRaises(KeyError):
            get_or_create_position(4, 'APPL', 'long', data_source=self.test_ds)
        # test get_or_create_position with incorrect symbol type and direction type/value
        with self.assertRaises(TypeError):
            get_or_create_position(1, 123, 'long', data_source=self.test_ds)
            get_or_create_position(1, 'APPL', 123, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            get_or_create_position(1, 'APPL', 'long123', data_source=self.test_ds)

        # test get_position_id function
        pos_id = get_position_ids(1, 'APPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, [1])
        pos_id = get_position_ids(1, 'APPL', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, [2])
        # test get_position_id with non-existing account id
        self.assertEqual(get_position_ids(4, 'APPL', 'long', data_source=self.test_ds), [])
        # test get_position_id with incorrect symbol type and direction type/value
        self.assertEqual(get_position_ids(1, 123, 'long', data_source=self.test_ds), [])
        self.assertEqual(get_position_ids(1, 'APPL', 123, data_source=self.test_ds), [])
        self.assertEqual(get_position_ids(1, 'APPL', 'long123', data_source=self.test_ds), [])

        # test get_position_by_id function
        position = get_position_by_id(1, data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'APPL')
        self.assertEqual(position['position'], 'long')
        self.assertEqual(position['qty'], 0)
        position = get_position_by_id(2, data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'APPL')
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
        self.assertEqual(positions.loc[1]['symbol'], 'APPL')
        self.assertEqual(positions.loc[1]['position'], 'long')
        self.assertEqual(positions.loc[1]['qty'], 0)
        self.assertEqual(positions.loc[2]['account_id'], 1)
        self.assertEqual(positions.loc[2]['symbol'], 'APPL')
        self.assertEqual(positions.loc[2]['position'], 'short')
        self.assertEqual(positions.loc[2]['qty'], 0)
        position = get_account_positions(2, data_source=self.test_ds)
        print(position)
        self.assertIsInstance(position, pd.DataFrame)
        self.assertEqual(len(position), 4)
        self.assertEqual(position.loc[3]['account_id'], 2)
        self.assertEqual(position.loc[3]['symbol'], 'APPL')
        self.assertEqual(position.loc[3]['position'], 'long')
        self.assertEqual(position.loc[3]['qty'], 0)
        self.assertEqual(position.loc[4]['account_id'], 2)
        self.assertEqual(position.loc[4]['symbol'], 'APPL')
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
        pos_id = get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 1)
        pos_id = get_or_create_position(1, 'APPL', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 2)
        pos_id = get_or_create_position(2, 'APPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 3)
        pos_id = get_or_create_position(2, 'APPL', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 4)
        pos_id = get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 5)
        pos_id = get_or_create_position(2, 'GOOG', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 6)
        # test update_position qty and available qty
        update_position(1, data_source=self.test_ds, qty_change=100)
        update_position(2, data_source=self.test_ds, qty_change=300)
        # check updated positions
        pos_id = get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 100)
        self.assertEqual(position['available_qty'], 0)
        pos_id = get_or_create_position(1, 'APPL', 'short', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 0)
        # update qty and available qty in the same time
        update_position(3, data_source=self.test_ds, qty_change=200, available_qty_change=100)
        update_position(4, data_source=self.test_ds, qty_change=300, available_qty_change=300)
        # check updated positions
        pos_id = get_or_create_position(2, 'APPL', 'long', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 200)
        self.assertEqual(position['available_qty'], 100)
        pos_id = get_or_create_position(2, 'APPL', 'short', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 300)
        # update qty and available qty on previous positions
        update_position(3, data_source=self.test_ds, qty_change=100, available_qty_change=-100)
        update_position(4, data_source=self.test_ds, qty_change=300, available_qty_change=100)
        # check updated positions
        pos_id = get_or_create_position(2, 'APPL', 'long', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 0)
        pos_id = get_or_create_position(2, 'APPL', 'short', data_source=self.test_ds)
        position = get_position_by_id(pos_id, data_source=self.test_ds)
        self.assertEqual(position['qty'], 600)
        self.assertEqual(position['available_qty'], 400)

        # update qty and available qty with bad values
        with self.assertRaises(RuntimeError):
            # not enough qty to reduce(own 300, reduce 400)
            update_position(3, data_source=self.test_ds, qty_change=-400, available_qty_change=100)
        with self.assertRaises(RuntimeError):
            # available qty will be less than 0
            update_position(4, data_source=self.test_ds, qty_change=300, available_qty_change=-500)
        with self.assertRaises(TypeError):
            # type does not match
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
        with self.assertRaises(TypeError):
            update_position(None, data_source=self.test_ds, qty_change=100, available_qty_change=100)
        with self.assertRaises(RuntimeError):
            update_position(100, data_source=self.test_ds, qty_change=100, available_qty_change=100)

    # test 2nd foundational function: get_account_availability / get_position_availability
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
        pos_id = get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
        self.assertEqual(pos_id, 1)
        pos_id = get_or_create_position(1, 'GOOG', 'short', data_source=self.test_ds)
        self.assertEqual(pos_id, 2)
        pos_id = get_or_create_position(2, 'APPL', 'long', data_source=self.test_ds)
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
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], 100000)
        self.assertEqual(res[1], 80000)
        self.assertEqual(res[2], 100000)
        res = get_account_cash_availabilities(account_id=2, data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0], 100000)
        self.assertEqual(res[1], 50000)
        self.assertEqual(res[2], 100000)

        # test get_account_position_availabilities function
        res = get_account_position_availabilities(account_id=1, shares=['APPL', 'GOOG'], data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 4)
        self.assertIsInstance(res[0], list)
        self.assertIsInstance(res[1], np.ndarray)
        self.assertIsInstance(res[2], np.ndarray)
        self.assertEqual(res[1].shape, (2,))
        self.assertEqual(res[2].shape, (2,))
        print(f'get_account_position_availabilities result: {res}')
        self.assertEqual(res[0], ['APPL', 'GOOG'])
        self.assertTrue(np.allclose(res[1], np.array([1000, -1000])))
        self.assertTrue(np.allclose(res[2], np.array([1000, -300])))
        res = get_account_position_availabilities(account_id=2, shares=['APPL', 'GOOG', 'MSFT', 'AMZN'],
                                                  data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 4)
        self.assertIsInstance(res[1], np.ndarray)
        self.assertIsInstance(res[2], np.ndarray)
        self.assertEqual(res[1].shape, (4,))
        self.assertEqual(res[2].shape, (4,))
        print(f'get_account_position_availabilities result: {res}')
        self.assertEqual(res[0], ['APPL', 'GOOG', 'MSFT', 'AMZN'])
        self.assertTrue(np.allclose(res[1], np.array([1000, 1000, -1000, -1000])))
        self.assertTrue(np.allclose(res[2], np.array([500, 1000, -700, -600])))
        res = get_account_position_availabilities(account_id=2,
                                                  shares=['APPL', 'FB', 'MSFT', 'AMZN', '000001'],
                                                  data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 4)
        self.assertIsInstance(res[1], np.ndarray)
        self.assertIsInstance(res[2], np.ndarray)
        self.assertEqual(res[1].shape, (5,))
        self.assertEqual(res[2].shape, (5,))
        print(f'get_account_position_availabilities result: {res}')
        self.assertEqual(res[0], ['APPL', 'FB', 'MSFT', 'AMZN', '000001'])
        self.assertTrue(np.allclose(res[1], np.array([1000, 0, -1000, -1000, 0])))
        self.assertTrue(np.allclose(res[2], np.array([500, 0, -700, -600, 0])))
        positions = get_account_position_details(account_id=2,
                                                 shares=['APPL', 'FB', 'MSFT', 'AMZN', '000001'],
                                                 data_source=self.test_ds)
        self.assertIsInstance(positions, pd.DataFrame)
        print(f'get_account_position_details result: {positions}')
        self.assertEqual(positions.shape, (3, 5))
        self.assertEqual(positions.columns.to_list(), ['APPL', 'FB', 'MSFT', 'AMZN', '000001'])
        self.assertTrue(np.allclose(positions.loc['qty'], np.array([1000, 0, -1000, -1000, 0])))
        self.assertTrue(np.allclose(positions.loc['available_qty'], np.array([500, 0, -700, -600, 0])))

        res = get_account_position_availabilities(account_id=2, data_source=self.test_ds)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 4)
        self.assertIsInstance(res[1], np.ndarray)
        self.assertIsInstance(res[2], np.ndarray)
        self.assertEqual(res[1].shape, (4,))
        print(f'get_account_position_availabilities result: {res}')
        self.assertTrue(np.allclose(res[1], np.array([1000, -1000, 1000, -1000])))
        self.assertTrue(np.allclose(res[2], np.array([500, -700, 1000, -600])))
        positions = get_account_position_details(account_id=2, data_source=self.test_ds)
        self.assertIsInstance(positions, pd.DataFrame)
        print(f'get_account_position_details result: {positions}')
        self.assertEqual(positions.shape, (3, 4))
        self.assertEqual(positions.columns.to_list(), ['APPL', 'MSFT', 'GOOG', 'AMZN'])
        self.assertTrue(np.allclose(positions.loc['qty'], np.array([1000, -1000, 1000, -1000])))
        self.assertTrue(np.allclose(positions.loc['available_qty'], np.array([500, -700, 1000, -600])))

    # test foundational functions related to signal generation and submission
    def test_record_read_and_update_orders(self):
        """ test record_and_read_signal function """
        # clear tables in test datasource if they existed
        if self.test_ds.table_data_exists('sys_op_trade_orders'):
            self.test_ds.drop_table_data('sys_op_trade_orders')
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')

        # writing test accounts and positions
        new_account(user_name='test_user', cash_amount=100000, data_source=self.test_ds)
        get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'MSFT', 'long', data_source=self.test_ds)
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
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'buy',
            'order_type':     'market',
            'qty':            200,
            'price':          10.0,
            'submitted_time': None,
            'status':         'created',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         3,
            'direction':      'sell',
            'order_type':     'market',
            'qty':            100,
            'price':          10.0,
            'submitted_time': None,
            'status':         'created',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        signal = read_trade_order(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        signal = read_trade_order(2, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 2)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 200)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        signal = read_trade_order(3, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 3)
        self.assertEqual(signal['direction'], 'sell')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 100)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        # test record signal with bad input
        with self.assertRaises(TypeError):
            record_trade_order(None, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            record_trade_order(1, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            record_trade_order('test', data_source=self.test_ds)
        bad_signal = {
            'account_id':     'a',
            'pos_id':         'a',
            'direction':      'buy',
            'order_type':     'market',
            'qty':            300,
            'price':          10.0,
            'submitted_time': None,
        }
        with self.assertRaises(TypeError):
            record_trade_order(bad_signal, data_source=self.test_ds)
        bad_signal = {
            'account_id': 1,
            'pos_id':     1,
            'direction':  'buy',
            'order_type': 'market',
            'qty':        -300,
            'price':      -10.0,
            'status':     'created',
        }
        with self.assertRaises(RuntimeError):
            record_trade_order(bad_signal, data_source=self.test_ds)
        # test read signal with bad input
        # self.assertIsNone(read_trade_order(None, data_source=self.test_ds))  # will return all signals
        with self.assertRaises(TypeError):
            read_trade_order(1.0, data_source=self.test_ds)
            read_trade_order('test', data_source=self.test_ds)
        self.assertEqual(read_trade_order(-1, data_source=self.test_ds), {})

        # test update signal
        update_trade_order(1, data_source=self.test_ds, status='submitted')
        signal = read_trade_order(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'submitted')
        update_trade_order(1, data_source=self.test_ds, status='partial-filled')
        signal = read_trade_order(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'partial-filled')
        update_trade_order(1, data_source=self.test_ds, status='filled')
        signal = read_trade_order(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'filled')
        update_trade_order(2, data_source=self.test_ds, status='canceled')
        signal = read_trade_order(2, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 2)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 200)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'created')
        update_trade_order(2, data_source=self.test_ds, status='submitted')
        signal = read_trade_order(2, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 2)
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 200)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'submitted')

        # test read trade signal details
        signal = read_trade_order_detail(1, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 1)
        self.assertEqual(signal['symbol'], 'APPL')
        self.assertEqual(signal['position'], 'long')
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 300)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'filled')
        signal = read_trade_order_detail(2, data_source=self.test_ds)
        self.assertIsInstance(signal, dict)
        self.assertEqual(signal['pos_id'], 2)
        self.assertEqual(signal['symbol'], 'MSFT')
        self.assertEqual(signal['position'], 'long')
        self.assertEqual(signal['direction'], 'buy')
        self.assertEqual(signal['order_type'], 'market')
        self.assertEqual(signal['qty'], 200)
        self.assertEqual(signal['price'], 10.0)
        self.assertEqual(signal['status'], 'submitted')
        signal = read_trade_order_detail(3, data_source=self.test_ds)
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
        signal = read_trade_order_detail(4, data_source=self.test_ds)
        self.assertIs(signal, None)
        # test read trade signal details with bad input
        with self.assertRaises(TypeError):
            read_trade_order_detail('1', data_source=self.test_ds)
            read_trade_order_detail(-1, data_source=self.test_ds)
            read_trade_order_detail(0, data_source=self.test_ds)
            read_trade_order_detail(999, data_source=self.test_ds)
            read_trade_order_detail(1.0, data_source=self.test_ds)

        # test update bad status
        with self.assertRaises(RuntimeError):
            update_trade_order(1, data_source=self.test_ds, status='test', raise_if_status_wrong=True)
            update_trade_order(1, data_source=self.test_ds, status='created', raise_if_status_wrong=True)
            update_trade_order(1, data_source=self.test_ds, status='submitted', raise_if_status_wrong=True)
            update_trade_order(1, data_source=self.test_ds, status='partial-filled', raise_if_status_wrong=True)
            update_trade_order(1, data_source=self.test_ds, status='filled', raise_if_status_wrong=True)
            update_trade_order(1, data_source=self.test_ds, status='test', raise_if_status_wrong=False)

        self.assertIsNone(
                update_trade_order(1, data_source=self.test_ds, status='created', raise_if_status_wrong=False)
        )
        self.assertIsNone(
                update_trade_order(1, data_source=self.test_ds, status='submitted', raise_if_status_wrong=False)
        )
        self.assertIsNone(
                update_trade_order(1, data_source=self.test_ds, status='partial-filled', raise_if_status_wrong=False)
        )
        self.assertIsNone(
                update_trade_order(1, data_source=self.test_ds, status='filled', raise_if_status_wrong=False)
        )

        # test update bad signal id
        with self.assertRaises(TypeError):
            update_trade_order('test', data_source=self.test_ds, status='submitted')

    def test_query_trade_orders(self):
        """ test query_trade_orders function """
        # clear tables in test datasource if they existed
        if self.test_ds.table_data_exists('sys_op_trade_orders'):
            self.test_ds.drop_table_data('sys_op_trade_orders')
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')

        # writing test accounts and positions
        new_account(user_name='test_user1', cash_amount=100000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=300000, data_source=self.test_ds)
        get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
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
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'buy',
            'order_type':     'market',
            'qty':            200,
            'price':          10.0,
            'submitted_time': None,
            'status':         'submitted',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         3,
            'direction':      'sell',
            'order_type':     'market',
            'qty':            100,
            'price':          10.0,
            'submitted_time': None,
            'status':         'filled',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'buy',
            'order_type':     'market',
            'qty':            300,
            'price':          15.0,
            'submitted_time': None,
            'status':         'submitted',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         3,
            'direction':      'buy',
            'order_type':     'market',
            'qty':            500,
            'price':          20.0,
            'submitted_time': None,
            'status':         'canceled',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         3,
            'direction':      'sell',
            'order_type':     'market',
            'qty':            200,
            'price':          20.0,
            'submitted_time': None,
            'status':         'partial-filled',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'sell',
            'order_type':     'market',
            'qty':            350,
            'price':          12.5,
            'submitted_time': None,
            'status':         'partial-filled',
        }
        record_trade_order(test_signal, data_source=self.test_ds)

        # test query all signals for a symbol and direction
        signals = query_trade_orders(1, symbol='APPL', position='long', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals['pos_id'].values[0], 1)
        self.assertEqual(signals['direction'].values[0], 'buy')
        self.assertEqual(signals['qty'].values[0], 300)
        self.assertEqual(signals['price'].values[0], 10.0)
        self.assertEqual(signals['status'].values[0], 'created')
        signals = query_trade_orders(1, symbol='GOOG', position='long', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 3)
        self.assertEqual(signals['pos_id'].values[0], 3)
        self.assertEqual(signals['direction'].values[0], 'sell')
        self.assertEqual(signals['qty'].values[0], 100)
        self.assertEqual(signals['price'].values[0], 10.0)
        self.assertEqual(signals['status'].values[0], 'filled')
        signals = query_trade_orders(1, symbol='GOOG', status='filled', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals['pos_id'].values[0], 3)
        self.assertEqual(signals['direction'].values[0], 'sell')
        self.assertEqual(signals['qty'].values[0], 100)
        self.assertEqual(signals['price'].values[0], 10.0)
        self.assertEqual(signals['status'].values[0], 'filled')
        signals = query_trade_orders(1, symbol='GOOG', status='canceled', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals['pos_id'].values[0], 3)
        self.assertEqual(signals['direction'].values[0], 'buy')
        self.assertEqual(signals['qty'].values[0], 500)
        self.assertEqual(signals['price'].values[0], 20.0)
        self.assertEqual(signals['status'].values[0], 'canceled')
        signals = query_trade_orders(2, symbol='MSFT', data_source=self.test_ds)
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
        signals = query_trade_orders(1, status='partial-filled', data_source=self.test_ds)
        print(signals)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals['pos_id'].values[0], 3)
        self.assertEqual(signals['direction'].values[0], 'sell')
        self.assertEqual(signals['qty'].values[0], 200)
        self.assertEqual(signals['price'].values[0], 20.0)
        self.assertEqual(signals['status'].values[0], 'partial-filled')
        signals = query_trade_orders(1, direction='buy', data_source=self.test_ds)
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
        signals = query_trade_orders(1, symbol='APPL', position='long', status='filled', data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)
        signals = query_trade_orders(1, symbol='invalid', position='long', status='filled', data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)
        signals = query_trade_orders(1, symbol='GOOG', position='invalid', status='filled', data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)
        signals = query_trade_orders(1, symbol='GOOG', position='long', status='invalid', data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)
        signals = query_trade_orders(1, symbol='GOOG', position='long', direction='invalid', data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)
        signals = query_trade_orders(999, symbol='GOOG', position='long', direction='buy', data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)
        signals = query_trade_orders(1, symbol=123, position='long', direction='buy', data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)
        signals = query_trade_orders(1, symbol='GOOG', position=123, direction='buy', data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)
        signals = query_trade_orders(1, symbol='GOOG', position='long', direction=123, data_source=self.test_ds)
        self.assertIsInstance(signals, pd.DataFrame)
        self.assertTrue(signals.empty)

    # test 2nd foundational functions: save_parsed_signals / submit_order / output_trade_order
    def test_save_parsed_orders(self):
        """ test save_parsed_signals function """
        # remove all data in test datasource
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        if self.test_ds.table_data_exists('sys_op_trade_orders'):
            self.test_ds.drop_table_data('sys_op_trade_orders')
        # create test accounts, positions should be created automatically with signals
        new_account(user_name='test_user1', cash_amount=100000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=150000, data_source=self.test_ds)
        # create test signals with parsed signals, which include list of symbols, positions, directions, qty, and prices
        # parsed signals has 5 symbols, with only long position, and buy direction
        parsed_signals = (
            ['GOOG', 'FB', 'APPL', 'AMZN', 'MSFT'],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'buy', 'buy', 'buy', 'buy'],
            [100, 200, 300, 400, 500],
            [10.0, 20.0, 30.0, 40.0, 50.0]
        )
        # save parsed signals
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals[0],
                positions=parsed_signals[1],
                directions=parsed_signals[2],
                quantities=parsed_signals[3],
                prices=parsed_signals[4],
                data_source=self.test_ds
        )
        # query signals from database
        self.assertEqual(len(order_ids), 5)
        signal_detail = read_trade_order_detail(order_ids[0], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 1)
        self.assertEqual(signal_detail['symbol'], 'GOOG')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 100)
        self.assertEqual(signal_detail['price'], 10.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_order_detail(order_ids[1], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 2)
        self.assertEqual(signal_detail['symbol'], 'FB')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 200)
        self.assertEqual(signal_detail['price'], 20.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_order_detail(order_ids[2], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 3)
        self.assertEqual(signal_detail['symbol'], 'APPL')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 300)
        self.assertEqual(signal_detail['price'], 30.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_order_detail(order_ids[3], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 4)
        self.assertEqual(signal_detail['symbol'], 'AMZN')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 400)
        self.assertEqual(signal_detail['price'], 40.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_order_detail(order_ids[4], data_source=self.test_ds)
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
        get_or_create_position(2, 'APPL', 'long', self.test_ds)  # pos_id = 8
        get_or_create_position(2, 'AMZN', 'long', self.test_ds)  # pos_id = 9
        get_or_create_position(2, 'MSFT', 'long', self.test_ds)  # pos_id = 10
        get_or_create_position(2, 'GOOG', 'short', self.test_ds)  # pos_id = 11
        get_or_create_position(2, 'FB', 'short', self.test_ds)  # pos_id = 12
        get_or_create_position(2, 'APPL', 'short', self.test_ds)  # pos_id = 13
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
            ['GOOG', 'FB', 'APPL', 'AMZN', 'MSFT'],
            ['long', 'long', 'short', 'short', 'long'],
            ['sell', 'buy', 'buy', 'sell', 'sell'],
            [100, 200, 300, 400, 500],
            [10.0, 20.0, 30.0, 40.0, 50.0]
        )
        order_ids = save_parsed_trade_orders(
                account_id=2,
                symbols=parsed_signals[0],
                positions=parsed_signals[1],
                directions=parsed_signals[2],
                quantities=parsed_signals[3],
                prices=parsed_signals[4],
                data_source=self.test_ds
        )
        # check signal detail
        self.assertEqual(len(order_ids), 5)
        signal_detail = read_trade_order_detail(order_ids[0], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 6)
        self.assertEqual(signal_detail['symbol'], 'GOOG')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'sell')
        self.assertEqual(signal_detail['qty'], 100)
        self.assertEqual(signal_detail['price'], 10.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_order_detail(order_ids[1], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 7)
        self.assertEqual(signal_detail['symbol'], 'FB')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 200)
        self.assertEqual(signal_detail['price'], 20.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_order_detail(order_ids[2], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 13)
        self.assertEqual(signal_detail['symbol'], 'APPL')
        self.assertEqual(signal_detail['position'], 'short')
        self.assertEqual(signal_detail['direction'], 'buy')
        self.assertEqual(signal_detail['qty'], 300)
        self.assertEqual(signal_detail['price'], 30.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_order_detail(order_ids[3], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 14)
        self.assertEqual(signal_detail['symbol'], 'AMZN')
        self.assertEqual(signal_detail['position'], 'short')
        self.assertEqual(signal_detail['direction'], 'sell')
        self.assertEqual(signal_detail['qty'], 400)
        self.assertEqual(signal_detail['price'], 40.0)
        self.assertEqual(signal_detail['status'], 'created')
        signal_detail = read_trade_order_detail(order_ids[4], data_source=self.test_ds)
        self.assertEqual(signal_detail['pos_id'], 10)
        self.assertEqual(signal_detail['symbol'], 'MSFT')
        self.assertEqual(signal_detail['position'], 'long')
        self.assertEqual(signal_detail['direction'], 'sell')
        self.assertEqual(signal_detail['qty'], 500)
        self.assertEqual(signal_detail['price'], 50.0)
        self.assertEqual(signal_detail['status'], 'created')
        # check position detail

    def test_submit_orders(self):
        """ test submit_order function """
        # remove all data in test datasource
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        if self.test_ds.table_data_exists('sys_op_trade_orders'):
            self.test_ds.drop_table_data('sys_op_trade_orders')
        # create test data, including two test accounts, 10 test positions, 5 for each account
        # create test accounts
        new_account(user_name='test_user1', cash_amount=100000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=150000, data_source=self.test_ds)
        # create test positions
        get_or_create_position(1, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'MSFT', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'AMZN', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'FB', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'APPL', 'long', data_source=self.test_ds)
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
            ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'sell', 'sell', 'buy', 'buy'],
            [100, 100, 300, 400, 500],
            [60.0, 70.0, 80.0, 90.0, 100.0],
        )
        # save first batch of signals
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch_1[0],
                positions=parsed_signals_batch_1[1],
                directions=parsed_signals_batch_1[2],
                quantities=parsed_signals_batch_1[3],
                prices=parsed_signals_batch_1[4],
                data_source=self.test_ds,
        )
        print('signal ids of first batch: {}'.format(order_ids))
        print(f'before submission, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        # submit first batch of signals one by one
        submit_order(1, data_source=self.test_ds)
        print(f'after submitting order 1, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty']
        aqty = position['available_qty']
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_order(2, data_source=self.test_ds)
        print(f'after submitting order 2, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_order(3, data_source=self.test_ds)
        print(f'after submitting order 3, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_order(4, data_source=self.test_ds)
        print(f'after submitting order 4, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_order(5, data_source=self.test_ds)
        print(f'after submitting order 5, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        # check status of all signals
        signal_detail = read_trade_order_detail(1, data_source=self.test_ds)
        print(f'signal_detail of signal 1: {signal_detail}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        self.assertEqual(signal_detail['status'], 'submitted')
        self.assertIsInstance(signal_detail['submitted_time'], (str, pd.Timestamp))

        # create second batch of signals, quantity exceeds available amount
        parsed_signals_batch_2 = (
            ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB'],
            ['long', 'long', 'long', 'long', 'long'],
            ['sell', 'sell', 'sell', 'buy', 'buy'],
            [100, 700, 800, 900, 1000],
            [10.0, 20.0, 30.0, 40.0, 50.0],
        )
        # save second batch of signals
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch_2[0],
                positions=parsed_signals_batch_2[1],
                directions=parsed_signals_batch_2[2],
                quantities=parsed_signals_batch_2[3],
                prices=parsed_signals_batch_2[4],
                data_source=self.test_ds,
        )
        print('signal ids of second batch: {}'.format(order_ids))
        print(f'before submission, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}')
        # submit second batch of signals one by one
        submit_order(6, data_source=self.test_ds)
        print(f'after submitting order 6, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        signal = read_trade_order_detail(6, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 100)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_order(7, data_source=self.test_ds)  # 此时需要卖出700股，但只有100股可用，按新规仅warning
        print(f'after submitting order 7, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        signal = read_trade_order_detail(7, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 700)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_order(8, data_source=self.test_ds)  # 此时需要卖出800股，但已经没有可用股份，按新规则仅warning
        print(f'after submitting order 8, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        signal = read_trade_order_detail(8, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 800)  # TODO, quantity is 0, 是否应该允许这种情况？
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_order(9, data_source=self.test_ds)  # 此时需要买入900股，但可用现金仅够买入200股，新规则仅warning
        print(f'after submitting order 9, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        signal = read_trade_order_detail(9, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 900)
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

        submit_order(10, data_source=self.test_ds)  # 此时已经没有可用现金
        print(f'after submitting order 10, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        cash_availabilities = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(cash_availabilities[0], 100000)
        self.assertEqual(cash_availabilities[1], 100000)
        signal = read_trade_order_detail(10, data_source=self.test_ds)
        self.assertEqual(signal['qty'], 1000)  # TODO, quantity is 0, 是否应该允许这种情况？
        position = get_account_positions(1, data_source=self.test_ds)
        qty = position['qty'].sort_index()
        aqty = position['available_qty'].sort_index()
        self.assertTrue(np.allclose(qty, [100, 200, 300, 400, 500]))
        self.assertTrue(np.allclose(aqty, [100, 200, 300, 400, 500]))

    def test_output_orders(self):
        """ test output_trade_order function """
        pass

    def test_read_and_write_result(self):
        """ test read_trade_result and write_trade_result functions """
        # 检查datasource中的数据表，删除所有的trade_result数据
        if self.test_ds.table_data_exists('sys_op_trade_results'):
            self.test_ds.drop_table_data('sys_op_trade_results')
        # 生成一个trade_result
        trade_result = {
            'order_id':        1,
            'filled_qty':      100.0,
            'price':           10.0,
            'transaction_fee': 5.0,
            'execution_time':  pd.to_datetime('now'),
            'canceled_qty':    0.0,
            'delivery_amount': 100.0,
            'delivery_status': 'ND',
        }
        # 将trade_result写入datasource
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        # 从datasource中读取trade_result
        trade_result = read_trade_result_by_id(result_id, data_source=self.test_ds)
        # 检查读取的trade_result是否与写入的trade_result一致
        self.assertIsInstance(trade_result, dict)
        self.assertEqual(trade_result['order_id'], 1)
        self.assertEqual(trade_result['filled_qty'], 100.0)
        self.assertEqual(trade_result['price'], 10.0)
        self.assertEqual(trade_result['transaction_fee'], 5.0)
        self.assertEqual(trade_result['canceled_qty'], 0.0)
        # 再次写入两个trade_results，order_id分别为1, 2，检查是否能正确读取order_id为1的两条交易结果
        trade_result = {
            'order_id':        1,
            'filled_qty':      200.0,
            'price':           10.5,
            'transaction_fee': 5.0,
            'execution_time':  pd.to_datetime('now'),
            'canceled_qty':    0.0,
            'delivery_amount': 200.0,
            'delivery_status': 'ND',
        }
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        self.assertEqual(result_id, 2)
        trade_result = {
            'order_id':        2,
            'filled_qty':      0.0,
            'price':           10.0,
            'transaction_fee': 5.0,
            'execution_time':  pd.to_datetime('now'),
            'canceled_qty':    100.0,
            'delivery_amount': 0.0,
            'delivery_status': 'ND',
        }
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        self.assertEqual(result_id, 3)
        trade_results = read_trade_results_by_order_id(order_id=1, data_source=self.test_ds)
        self.assertIsInstance(trade_results, pd.DataFrame)
        self.assertEqual(len(trade_results), 2)
        self.assertEqual(trade_results['order_id'].loc[1], 1)
        self.assertEqual(trade_results['order_id'].loc[2], 1)
        self.assertEqual(trade_results['filled_qty'].loc[1], 100.0)
        self.assertEqual(trade_results['filled_qty'].loc[2], 200.0)
        self.assertEqual(trade_results['price'].loc[1], 10.0)
        self.assertEqual(trade_results['price'].loc[2], 10.5)
        self.assertEqual(trade_results['transaction_fee'].loc[1], 5.0)
        self.assertEqual(trade_results['transaction_fee'].loc[2], 5.0)
        self.assertEqual(trade_results['canceled_qty'].loc[1], 0.0)
        self.assertEqual(trade_results['canceled_qty'].loc[2], 0.0)
        # test update_trade_result
        trade_result = read_trade_result_by_id(1, data_source=self.test_ds)
        self.assertEqual(trade_result['delivery_status'], 'ND')
        update_trade_result(1, delivery_status='DL', data_source=self.test_ds)
        trade_result = read_trade_result_by_id(1, data_source=self.test_ds)
        self.assertEqual(trade_result['delivery_status'], 'DL')
        # test update trade result with bad input
        with self.assertRaises(TypeError):
            update_trade_result(None, delivery_status='DL', data_source=self.test_ds)
        with self.assertRaises(TypeError):
            update_trade_result(1, delivery_status=2, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            update_trade_result(1, delivery_status='Invalid Status', data_source=None)

        # test write_trade_result with bad input
        with self.assertRaises(TypeError):
            write_trade_result(None, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'order_id':        '1',
                'filled_qty':      200.0,
                'price':           10.5,
                'transaction_fee': 5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    0.0,
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'order_id':        1,
                'filled_qty':      '200.0',
                'price':           10.5,
                'transaction_fee': 5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    0.0,
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'order_id':        1,
                'filled_qty':      200.0,
                'price':           '10.5',
                'transaction_fee': 5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    0.0,
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'order_id':        1,
                'filled_qty':      200.0,
                'price':           10.5,
                'transaction_fee': '5.0',
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    0.0,
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)
        with self.assertRaises(TypeError):
            write_trade_result({
                'order_id':        1,
                'filled_qty':      200.0,
                'price':           10.5,
                'transaction_fee': 5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    '0.0',
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'order_id':        -1,
                'filled_qty':      200.0,
                'price':           10.5,
                'transaction_fee': 5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    0.0,
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'order_id':        1,
                'filled_qty':      -200.0,
                'price':           10.5,
                'transaction_fee': 5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    0.0,
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'order_id':        1,
                'filled_qty':      200.0,
                'price':           -10.5,
                'transaction_fee': 5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    0.0,
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'order_id':        1,
                'filled_qty':      200.0,
                'price':           10.5,
                'transaction_fee': -5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    0.0,
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)
        with self.assertRaises(ValueError):
            write_trade_result({
                'order_id':        1,
                'filled_qty':      200.0,
                'price':           10.5,
                'transaction_fee': 5.0,
                'execution_time':  pd.to_datetime('now'),
                'canceled_qty':    -100.0,
                'delivery_amount': 200.0,
                'delivery_status': 'ND',
            }, data_source=self.test_ds)

    def test_delete_account(self):
        """ test function delete_account """
        # create and add test accounts, positions, trade orders and trade results
        new_account(user_name='test_user1', cash_amount=100000, data_source=self.test_ds)
        new_account(user_name='test_user2', cash_amount=150000, data_source=self.test_ds)
        get_or_create_position(1, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'APPL', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'MSFT', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'AMZN', 'long', data_source=self.test_ds)
        get_or_create_position(1, 'FB', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'GOOG', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'APPL', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'MSFT', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'AMZN', 'long', data_source=self.test_ds)
        get_or_create_position(2, 'FB', 'long', data_source=self.test_ds)
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
        parsed_signals_batch_1 = (
            ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'sell', 'sell', 'buy', 'buy'],
            [100, 100, 100, 100, 100],
            [60.0, 70.0, 80.0, 90.0, 100.0],
        )
        # create trade orders for account 1
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch_1[0],
                positions=parsed_signals_batch_1[1],
                directions=parsed_signals_batch_1[2],
                quantities=parsed_signals_batch_1[3],
                prices=parsed_signals_batch_1[4],
                data_source=self.test_ds,
        )
        orders_created = query_trade_orders(account_id=1, data_source=self.test_ds)
        print(f'orders_written: {order_ids}\norders_read: \n{orders_created}')
        # create trade orders for account 2
        parsed_signals_batch_2 = (
            ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'sell', 'sell', 'buy', 'buy'],
            [200, 200, 200, 200, 200],
            [60.0, 70.0, 80.0, 90.0, 100.0],
        )
        order_ids = save_parsed_trade_orders(
                account_id=2,
                symbols=parsed_signals_batch_2[0],
                positions=parsed_signals_batch_2[1],
                directions=parsed_signals_batch_2[2],
                quantities=parsed_signals_batch_2[3],
                prices=parsed_signals_batch_2[4],
                data_source=self.test_ds,
        )
        orders_created = query_trade_orders(account_id=2, data_source=self.test_ds)
        print(f'orders_written: {order_ids}\norders_read: \n{orders_created}')
        # create trade results for account 1
        trade_result = {
            'order_id':        1,
            'filled_qty':      100.0,
            'price':           10.0,
            'transaction_fee': 5.0,
            'execution_time':  pd.to_datetime('now'),
            'canceled_qty':    0.0,
            'delivery_amount': 100.0,
            'delivery_status': 'ND',
        }
        # 将trade_result写入datasource
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        trade_result = {
            'order_id':        2,
            'filled_qty':      200.0,
            'price':           10.5,
            'transaction_fee': 5.0,
            'execution_time':  pd.to_datetime('now'),
            'canceled_qty':    0.0,
            'delivery_amount': 200.0,
            'delivery_status': 'ND',
        }
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        # create trade results for account 2
        trade_result = {
            'order_id':        6,
            'filled_qty':      200.0,
            'price':           10.0,
            'transaction_fee': 5.0,
            'execution_time':  pd.to_datetime('now'),
            'canceled_qty':    0.0,
            'delivery_amount': 300.0,
            'delivery_status': 'ND',
        }
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        trade_result = {
            'order_id':        7,
            'filled_qty':      200.0,
            'price':           10.5,
            'transaction_fee': 5.0,
            'execution_time':  pd.to_datetime('now'),
            'canceled_qty':    0.0,
            'delivery_amount': 400.0,
            'delivery_status': 'ND',
        }
        result_id = write_trade_result(trade_result, data_source=self.test_ds)
        # read all data from tables and print to check
        print(f'before deleting:')
        accounts = self.test_ds.read_sys_table_data('sys_op_live_accounts')
        positions = self.test_ds.read_sys_table_data('sys_op_positions')
        orders = self.test_ds.read_sys_table_data('sys_op_trade_orders')
        results = self.test_ds.read_sys_table_data('sys_op_trade_results')
        print(f'accounts: \n{accounts}\npositions: \n{positions}\norders: \n{orders}\nresults: \n{results}')
        self.assertEqual(accounts.index.to_list(), [1, 2])
        self.assertEqual(positions.index.to_list(), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(orders.index.to_list(), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(results.index.to_list(), [1, 2, 3, 4])
        # delete account 2 while keeping account_id
        delete_account(2, data_source=self.test_ds, keep_account_id=True)
        # read all data from tables and print to check
        print(f'after deleting:')
        accounts = self.test_ds.read_sys_table_data('sys_op_live_accounts')
        positions = self.test_ds.read_sys_table_data('sys_op_positions')
        orders = self.test_ds.read_sys_table_data('sys_op_trade_orders')
        results = self.test_ds.read_sys_table_data('sys_op_trade_results')
        print(f'accounts: \n{accounts}\npositions: \n{positions}\norders: \n{orders}\nresults: \n{results}')
        self.assertEqual(accounts.index.to_list(), [1, 2])
        self.assertEqual(positions.index.to_list(), [1, 2, 3, 4, 5])
        self.assertEqual(orders.index.to_list(), [1, 2, 3, 4, 5])
        self.assertEqual(results.index.to_list(), [1, 2])
        # test fail to delete account with bad input
        with self.assertRaises(TypeError):
            delete_account('1', data_source=self.test_ds)
            delete_account(None, data_source=self.test_ds)
            delete_account(1, data_source='not_a_datasource')
            delete_account(-1, data_source=self.test_ds)
            delete_account(3, data_source=self.test_ds)


class TestTradingUtilFuncs(unittest.TestCase):
    """ test trading util funcs """

    def setUp(self):
        """ execute before each test"""
        from qteasy import QT_ROOT_PATH, QT_CONFIG
        self.qt_root_path = QT_ROOT_PATH
        self.data_test_dir = '../qteasy/data_test/'
        QT_CONFIG['hist_dnld_retry_cnt'] = 2  # 减少重试次数，加快测试速度
        # 创建一个专用的测试数据源，以免与已有的文件混淆，不需要测试所有的数据源，因为相关测试在test_datasource中已经完成
        self.test_ds = DataSource(
                'file',
                file_type='hdf',
                file_loc=self.data_test_dir,
                allow_drop_table=True,
        )

        # 清空测试数据源中的所有相关表格数据
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_orders']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)

    def test_create_daily_task_agenda(self):
        """ test function create_daily_task_schedule """
        # test create daily task agenda with only one strategy, run_freq='d', run_timing='close'
        op = qt.Operator(strategies='macd')
        stg = op.strategies[0]
        self.assertEqual(stg.strategy_run_freq, 'd')
        self.assertEqual(stg.strategy_run_timing, 'close')
        config = {
            'market_open_time_am':               '09:30:00',
            'market_close_time_pm':              '15:30:00',
            'market_open_time_pm':               '13:00:00',
            'market_close_time_am':              '11:30:00',
            'exchange':                          'SSE',
            'strategy_open_close_timing_offset': 1,
            'live_price_acquire_freq':           '15min',
            'live_trade_daily_refill_tables':    'stock_1min',
            'live_trade_weekly_refill_tables':   'stock_15min',
            'live_trade_monthly_refill_tables':  'stock_daily',
        }
        agenda = create_daily_task_schedule(op, config)
        print([f'{i}: {item}' for i, item in enumerate(agenda)])
        self.assertIsInstance(agenda, list)
        self.assertEqual(len(agenda), 26)
        self.assertEqual(agenda[0], ('09:15:00', 'pre_open'))
        self.assertEqual(agenda[1], ('09:30:00', 'open_market'))
        self.assertEqual(agenda[2], ('09:45:05', 'acquire_live_price'))
        self.assertEqual(agenda[3], ('10:00:05', 'acquire_live_price'))
        self.assertEqual(agenda[9], ('11:30:05', 'acquire_live_price'))
        self.assertEqual(agenda[10], ('11:35:00', 'close_market'))
        self.assertEqual(agenda[11], ('12:55:00', 'open_market'))
        self.assertEqual(agenda[12], ('13:15:05', 'acquire_live_price'))
        self.assertEqual(agenda[19], ('15:00:05', 'acquire_live_price'))
        self.assertEqual(agenda[21], ('15:29:00', 'run_strategy', ['macd']))
        self.assertEqual(agenda[22], ('15:30:00', 'close_market'))
        self.assertEqual(agenda[23], ('15:30:05', 'acquire_live_price'))
        self.assertEqual(agenda[24], ('15:45:00', 'post_close'))
        self.assertEqual(agenda[25], ('16:00:00', 'refill', ('stock_1min', 1)))

        # test create daily task agenda with only one strategy, run_freq='h', run_timing='open'
        op = qt.Operator(strategies='macd')
        stg = op.strategies[0]
        stg.strategy_run_freq = 'h'
        stg.strategy_run_timing = 'open'
        config = {
            'market_open_time_am':               '09:30:00',
            'market_close_time_pm':              '15:30:00',
            'market_open_time_pm':               '13:00:00',
            'market_close_time_am':              '11:30:00',
            'exchange':                          'SSE',
            'strategy_open_close_timing_offset': 1,
            'live_price_acquire_freq':           '15min',
            'live_trade_daily_refill_tables':    'stock_1min, stock_5min',
            'live_trade_weekly_refill_tables':   'stock_15min',
            'live_trade_monthly_refill_tables':  'stock_daily',
        }
        agenda = create_daily_task_schedule(op, config)
        print([f'{i}: {item}' for i, item in enumerate(agenda)])
        self.assertIsInstance(agenda, list)
        self.assertEqual(len(agenda), 31)
        self.assertEqual(agenda[0], ('09:15:00', 'pre_open'))
        self.assertEqual(agenda[1], ('09:30:00', 'open_market'))
        self.assertEqual(agenda[2], ('09:31:00', 'run_strategy', ['macd']))  # 本应该在9:30运行，但是按照规则开盘时推迟一分钟
        self.assertEqual(agenda[3], ('09:45:05', 'acquire_live_price'))
        self.assertEqual(agenda[6], ('10:30:00', 'run_strategy', ['macd']))
        self.assertEqual(agenda[11], ('11:30:00', 'run_strategy', ['macd']))
        self.assertEqual(agenda[13], ('11:35:00', 'close_market'))
        self.assertEqual(agenda[14], ('12:55:00', 'open_market'))
        self.assertEqual(agenda[15], ('13:00:00', 'run_strategy', ['macd']))
        self.assertEqual(agenda[19], ('14:00:00', 'run_strategy', ['macd']))
        self.assertEqual(agenda[24], ('15:00:00', 'run_strategy', ['macd']))
        self.assertEqual(agenda[27], ('15:30:00', 'close_market'))
        self.assertEqual(agenda[28], ('15:30:05', 'acquire_live_price'))
        self.assertEqual(agenda[29], ('15:45:00', 'post_close'))
        self.assertEqual(agenda[30], ('16:00:00', 'refill', ('stock_1min, stock_5min', 1)))

        # test create daily task agenda with multiple strategies, run_freq='h'/'30min'/'d', run_timing='//10:30'
        op = qt.Operator(strategies=['macd', 'rsi', 'dma'])
        stg = op.strategies[0]
        stg.strategy_run_freq = 'h'
        stg.strategy_run_timing = 'open'
        stg = op.strategies[1]
        stg.strategy_run_freq = '30min'
        stg.strategy_run_timing = 'open'
        stg = op.strategies[2]
        stg.strategy_run_freq = 'd'
        stg.strategy_run_timing = '10:30'
        config = {
            'market_open_time_am':               '09:30:00',
            'market_close_time_pm':              '15:30:00',
            'market_open_time_pm':               '13:00:00',
            'market_close_time_am':              '11:30:00',
            'exchange':                          'SSE',
            'strategy_open_close_timing_offset': 1,
            'live_price_acquire_freq':           '60min',
            'live_trade_daily_refill_tables':    'stock_1min',
            'live_trade_weekly_refill_tables':   'stock_15min',
            'live_trade_monthly_refill_tables':  'stock_daily',
        }
        agenda = create_daily_task_schedule(op, config)
        print([f'{i}: {item}' for i, item in enumerate(agenda)])
        self.assertIsInstance(agenda, list)
        self.assertEqual(len(agenda), 22)
        self.assertEqual(agenda[0], ('09:15:00', 'pre_open'))
        self.assertEqual(agenda[1], ('09:30:00', 'open_market'))
        self.assertEqual(agenda[2], ('09:31:00', 'run_strategy', ['macd', 'rsi']))
        self.assertEqual(agenda[3], ('10:00:00', 'run_strategy', ['rsi']))
        self.assertEqual(agenda[4], ('10:00:05', 'acquire_live_price'))
        self.assertEqual(agenda[5], ('10:30:00', 'run_strategy', ['macd', 'rsi', 'dma']))
        self.assertEqual(agenda[6], ('11:00:00', 'run_strategy', ['rsi']))
        self.assertEqual(agenda[7], ('11:00:05', 'acquire_live_price'))
        self.assertEqual(agenda[8], ('11:30:00', 'run_strategy', ['macd', 'rsi']))
        self.assertEqual(agenda[9], ('11:35:00', 'close_market'))
        self.assertEqual(agenda[10], ('12:55:00', 'open_market'))
        self.assertEqual(agenda[11], ('13:00:00', 'run_strategy', ['macd', 'rsi']))
        self.assertEqual(agenda[12], ('13:30:00', 'run_strategy', ['rsi']))
        self.assertEqual(agenda[13], ('14:00:00', 'run_strategy', ['macd', 'rsi']))
        self.assertEqual(agenda[14], ('14:00:05', 'acquire_live_price'))
        self.assertEqual(agenda[15], ('14:30:00', 'run_strategy', ['rsi']))
        self.assertEqual(agenda[16], ('15:00:00', 'run_strategy', ['macd', 'rsi']))
        self.assertEqual(agenda[17], ('15:00:05', 'acquire_live_price'))
        self.assertEqual(agenda[18], ('15:29:00', 'run_strategy', ['rsi']))
        self.assertEqual(agenda[19], ('15:30:00', 'close_market'))
        self.assertEqual(agenda[20], ('15:45:00', 'post_close'))
        self.assertEqual(agenda[21], ('16:00:00', 'refill', ('stock_1min', 1)))

    def test_process_trade_orders(self):
        """ test full process of trading:
        1, order generation,
        2, order submission,
        3, result processing and delivery
        4, last_trade_result_summary
        """
        # 检查datasource中的数据表，删除所有的account, positions, trade_signal, trade_result数据
        if self.test_ds.table_data_exists('sys_op_live_accounts'):
            self.test_ds.drop_table_data('sys_op_live_accounts')
        if self.test_ds.table_data_exists('sys_op_positions'):
            self.test_ds.drop_table_data('sys_op_positions')
        if self.test_ds.table_data_exists('sys_op_trade_orders'):
            self.test_ds.drop_table_data('sys_op_trade_orders')
        if self.test_ds.table_data_exists('sys_op_trade_results'):
            self.test_ds.drop_table_data('sys_op_trade_results')
        # 重新创建account及trade_signal数据, position会在submit_signal中自动创建
        delivery_config = {
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
        }
        # create test accounts
        new_account(user_name='test_user1', cash_amount=100000, data_source=self.test_ds)
        # create test trade signals
        # create test signals, all signals are buy signals, because the test starts with zero positions
        parsed_signals_batch_1 = (
            ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'buy', 'buy', 'buy', 'buy'],
            [100, 100, 300, 400, 500],
            [60.0, 70.0, 80.0, 90.0, 30.0],
        )
        # save first batch of trade orders
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch_1[0],
                positions=parsed_signals_batch_1[1],
                directions=parsed_signals_batch_1[2],
                quantities=parsed_signals_batch_1[3],
                prices=parsed_signals_batch_1[4],
                data_source=self.test_ds,
        )
        self.assertEqual(order_ids, [1, 2, 3, 4, 5])
        # 交易订单已经保存，但订单状态为“created”，尚未提交，此时订单不会生效
        # 逐个提交交易信号并打印相关余额的变化
        submit_order(1, data_source=self.test_ds)
        print(f'after submitting order 1, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        submit_order(2, data_source=self.test_ds)
        print(f'after submitting order 2, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        submit_order(3, data_source=self.test_ds)
        print(f'after submitting order 3, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        submit_order(4, data_source=self.test_ds)
        print(f'after submitting order 4, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')
        submit_order(5, data_source=self.test_ds)
        print(f'after submitting order 5, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}')

        # test last_trade_result_summary with no share (at this moment, there is no trade result yet, all zero values)
        summary = get_last_trade_result_summary(1, data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB', ])
        self.assertEqual(list(summary[1]), [0, 0, 0, 0, 0])
        self.assertEqual(list(summary[2]), [0, 0, 0, 0, 0])

        # test last_trade_result_summary with share
        summary = get_last_trade_result_summary(1, shares=['GOOG', 'APPL', 'AMZN'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN"]: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'AMZN', ])
        self.assertEqual(list(summary[1]), [0, 0, 0])
        self.assertEqual(list(summary[2]), [0, 0, 0])
        summary = get_last_trade_result_summary(1, shares=['FB', 'APPL', 'FB'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["FB", "GOOG", "FB"]: \n{summary}')
        self.assertEqual(summary[0], ['FB', 'APPL', 'FB', ])
        self.assertEqual(list(summary[1]), [0, 0, 0])
        self.assertEqual(list(summary[2]), [0, 0, 0])

        # test last_trade_result_summary with share out of range
        summary = get_last_trade_result_summary(1, shares=['GOOG', 'AMZN', 'TSLA'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["APPL", "GOOG", "TSLA"]: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'AMZN', 'TSLA', ])
        self.assertEqual(list(summary[1]), [0, 0, 0])
        self.assertEqual(list(summary[2]), [0, 0, 0])

        # 生成交易结果并逐个处理, 注意raw_results没有execution_time字段
        # signal 1 is filled with 100 shares at 60.5, transaction fee is 5.0
        raw_trade_result = {
            'order_id':        1,
            'filled_qty':      100,
            'price':           60.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        print(f'\n------------START PROCESS TRADE RESULT-----------------\n'
              f'before processing trade result 1, trade signal: \n'
              f'{read_trade_order_detail(1, data_source=self.test_ds)}\n')
        process_account_delivery(account_id=1, data_source=self.test_ds, config=delivery_config)
        process_trade_result(raw_trade_result, data_source=self.test_ds)
        print(f'after processing trade result 1, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}\n'
              f'trade_signal_detail of order_id == 1: \n'
              f'{read_trade_order_detail(1, data_source=self.test_ds)}\n'
              f'trade_result_detail of order_id == 1: \n'
              f'{read_trade_results_by_order_id(1, data_source=self.test_ds).loc[1].to_dict()}')
        trade_result = read_trade_result_by_id(1, data_source=self.test_ds)
        # check cash availability
        own_cash, available_cash, total_invest = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(own_cash, 100000.0 - 100 * 60.5 - 5.0)
        self.assertEqual(available_cash, 100000.0 - 100 * 60.5 - 5.0)
        self.assertEqual(total_invest, 100000.0)
        trade_signal_detail = read_trade_order_detail(1, data_source=self.test_ds)
        # check available qty availability
        symbols, own_qty, available_qty, costs = get_account_position_availabilities(
                1,
                trade_signal_detail['symbol'],
                data_source=self.test_ds,
        )
        self.assertEqual(int(own_qty), 0.0 + 100.0)
        self.assertEqual(int(available_qty), 0.0 + 0.0)
        self.assertEqual(float(costs), (5.0 + 100.0 * 60.5) / 100)
        # check trade_signal status
        self.assertEqual(trade_signal_detail['status'], 'filled')
        # check trade result status
        self.assertEqual(trade_result['delivery_amount'], 100)
        self.assertEqual(trade_result['delivery_status'], 'ND')
        # check trade result summary with no share
        summary = get_last_trade_result_summary(1, data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with no shares: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB'])
        self.assertEqual(list(summary[1]), [100, 0, 0, 0, 0])
        self.assertEqual(list(summary[2]), [60.5, 0, 0, 0, 0])
        # check trade result summary with share
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'AMZN'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'AMZN'])
        self.assertEqual(list(summary[1]), [0, 100, 0])
        self.assertEqual(list(summary[2]), [0, 60.5, 0])

        # order 2 is canceled with no transaction fee
        raw_trade_result = {
            'order_id':        2,
            'filled_qty':      0,
            'price':           0.0,
            'transaction_fee': 0.0,
            'canceled_qty':    100.0,
        }
        print(f'\n------------START PROCESS TRADE RESULT-----------------\n'
              f'before processing trade result 2, trade signal: \n'
              f'{read_trade_order_detail(2, data_source=self.test_ds)}\n')
        process_account_delivery(account_id=1, data_source=self.test_ds, config=delivery_config)
        process_trade_result(raw_trade_result, data_source=self.test_ds)
        print(f'after processing trade result 2, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}\n'
              f'trade_signal_detail of order_id == 2: \n'
              f'{read_trade_order_detail(2, data_source=self.test_ds)}\n'
              f'trade_result_detail of order_id == 2: \n'
              f'{read_trade_results_by_order_id(2, data_source=self.test_ds).loc[2].to_dict()}')
        trade_result = read_trade_result_by_id(2, data_source=self.test_ds)
        # check cash availability
        own_cash, available_cash, total_invest = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(own_cash, 100000.0 - 100 * 60.5 - 5.0)
        self.assertEqual(available_cash, 100000.0 - 100 * 60.5 - 5.0)
        self.assertEqual(total_invest, 100000.0)
        trade_signal_detail = read_trade_order_detail(2, data_source=self.test_ds)
        # check available qty availability
        symbols, own_qty, available_qty, costs = get_account_position_availabilities(
                1,
                trade_signal_detail['symbol'],
                data_source=self.test_ds,
        )
        self.assertEqual(int(own_qty), 0.0 + 0.0)
        self.assertEqual(int(available_qty), 0.0 + 0.0)
        self.assertEqual(float(costs), 0.0)
        # check trade_signal status
        self.assertEqual(trade_signal_detail['status'], 'canceled')
        # check trade result status
        self.assertEqual(trade_result['delivery_amount'], 0)
        self.assertEqual(trade_result['delivery_status'], 'ND')
        # check trade result summary with no share
        summary = get_last_trade_result_summary(1, data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with no shares: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB'])
        self.assertEqual(list(summary[1]), [100, 0, 0, 0, 0])
        self.assertEqual(list(summary[2]), [60.5, 0, 0, 0, 0])
        # check trade result summary with share
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'AMZN'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'AMZN'])
        self.assertEqual(list(summary[1]), [0, 100, 0])
        self.assertEqual(list(summary[2]), [0, 60.5, 0])
        # check trade result summary with share that out of range
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'AMZN', 'FB'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN", "FB"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'AMZN', 'FB'])
        self.assertEqual(list(summary[1]), [0, 100, 0, 0])
        self.assertEqual(list(summary[2]), [0, 60.5, 0, 0])

        # signal 3 is partially filled with 100 shares bought at 81, with transaction fee 12.5
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      100.0,
            'price':           81.0,
            'transaction_fee': 12.5,
            'canceled_qty':    0.0,
        }
        print(f'\n------------START PROCESS TRADE RESULT-----------------\n'
              f'before processing trade result 3, trade signal: \n'
              f'{read_trade_order_detail(3, data_source=self.test_ds)}\n')
        process_account_delivery(account_id=1, data_source=self.test_ds, config=delivery_config)
        process_trade_result(raw_trade_result, data_source=self.test_ds)
        print(f'after processing trade result 3, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}\n'
              f'trade_signal_detail of order_id == 3: \n'
              f'{read_trade_order_detail(3, data_source=self.test_ds)}\n'
              f'trade_result_detail of order_id == 3: \n'
              f'{read_trade_results_by_order_id(3, data_source=self.test_ds).loc[3].to_dict()}')
        trade_result = read_trade_result_by_id(3, data_source=self.test_ds)
        # check cash availability
        own_cash, available_cash, total_invest = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(own_cash, 100000.0 - 100 * 60.5 - 5.0 - 100 * 81.0 - 12.5)
        self.assertEqual(available_cash, 100000.0 - 100 * 60.5 - 5.0 - 100 * 81.0 - 12.5)
        self.assertAlmostEqual(total_invest, 100000.0)
        trade_signal_detail = read_trade_order_detail(3, data_source=self.test_ds)
        # check available qty availability
        symbols, own_qty, available_qty, costs = get_account_position_availabilities(
                1,
                trade_signal_detail['symbol'],
                data_source=self.test_ds,
        )
        self.assertEqual(int(own_qty), 0.0 + 100.0)
        self.assertEqual(int(available_qty), 0.0 + 0.0)
        self.assertEqual(float(costs), (100.0 * 81.0 + 12.5) / 100)
        # check trade_signal status
        self.assertEqual(trade_signal_detail['status'], 'partial-filled')
        # check trade result status
        self.assertEqual(trade_result['delivery_amount'], 100)
        self.assertEqual(trade_result['delivery_status'], 'ND')
        # check trade result summary with no share
        summary = get_last_trade_result_summary(1, data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with no shares: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB'])
        self.assertEqual(list(summary[1]), [100, 0, 100, 0, 0])
        self.assertEqual(list(summary[2]), [60.5, 0, 81, 0, 0])
        # check trade result summary with share
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'AMZN'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'AMZN'])
        self.assertEqual(list(summary[1]), [0, 100, 0])
        self.assertEqual(list(summary[2]), [0, 60.5, 0])
        # check trade result summary with share that out of range
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'MSFT', 'FB'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "MSFT", "FB"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'MSFT', 'FB'])
        self.assertEqual(list(summary[1]), [0, 100, 100, 0])
        self.assertEqual(list(summary[2]), [0, 60.5, 81, 0])

        # signal 4 is filled with 400 shares bought at 89.5, with transaction fee 7.5
        raw_trade_result = {
            'order_id':        4,
            'filled_qty':      400.0,
            'price':           89.5,
            'transaction_fee': 7.5,
            'canceled_qty':    0.0,
        }
        print(f'\n------------START PROCESS TRADE RESULT-----------------\n'
              f'before processing trade result 4, trade signal: \n'
              f'{read_trade_order_detail(4, data_source=self.test_ds)}\n')
        process_account_delivery(account_id=1, data_source=self.test_ds, config=delivery_config)
        process_trade_result(raw_trade_result, data_source=self.test_ds)
        print(f'after processing trade result 4, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}\n'
              f'trade_signal_detail of order_id == 4: \n'
              f'{read_trade_order_detail(4, data_source=self.test_ds)}\n'
              f'trade_result_detail of order_id == 4: \n'
              f'{read_trade_results_by_order_id(4, data_source=self.test_ds).loc[4].to_dict()}')
        trade_result = read_trade_result_by_id(4, data_source=self.test_ds)
        # check cash availability
        own_cash, available_cash, total_invest = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(own_cash, 100000.0 - 100 * 60.5 - 5.0 - 100 * 81.0 - 12.5 - 400 * 89.5 - 7.5)
        self.assertEqual(available_cash, 100000.0 - 100 * 60.5 - 5.0 - 100 * 81.0 - 12.5 - 400 * 89.5 - 7.5)
        self.assertAlmostEqual(total_invest, 100000.0)
        trade_signal_detail = read_trade_order_detail(4, data_source=self.test_ds)
        # check available qty availability
        symbols, own_qty, available_qty, costs = get_account_position_availabilities(
                1,
                trade_signal_detail['symbol'],
                data_source=self.test_ds,
        )
        self.assertEqual(int(own_qty), 0.0 + 400.0)
        self.assertEqual(int(available_qty), 0.0 + 0.0)
        self.assertEqual(float(costs), (7.5 + 400.0 * 89.5) / 400)
        # check trade_signal status
        self.assertEqual(trade_signal_detail['status'], 'filled')
        # check trade result status
        self.assertEqual(trade_result['delivery_amount'], 400)
        self.assertEqual(trade_result['delivery_status'], 'ND')
        # check trade result summary with no share
        summary = get_last_trade_result_summary(1, data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with no shares: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB'])
        self.assertEqual(list(summary[1]), [100, 0, 100, 400, 0])
        self.assertEqual(list(summary[2]), [60.5, 0, 81, 89.5, 0])
        # check trade result summary with share
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'AMZN'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'AMZN'])
        self.assertEqual(list(summary[1]), [0, 100, 400])
        self.assertEqual(list(summary[2]), [0, 60.5, 89.5])
        # check trade result summary with share that out of range
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'MSFT', 'FB'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "MSFT", "FB"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'MSFT', 'FB'])
        self.assertEqual(list(summary[1]), [0, 100, 100, 0])
        self.assertEqual(list(summary[2]), [0, 60.5, 81, 0])

        # create more test orders, with sell orders
        parsed_signals_batch_1 = (
            ['APPL', 'GOOG', 'MSFT', 'AMZN', 'FB', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['sell', 'sell', 'sell', 'sell', 'sell'],
            [100, 100, 300, 400, 500],
            [90.0, 90.0, 90.0, 120.0, 30.0],
        )
        # save first batch of signals
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch_1[0],
                positions=parsed_signals_batch_1[1],
                directions=parsed_signals_batch_1[2],
                quantities=parsed_signals_batch_1[3],
                prices=parsed_signals_batch_1[4],
                data_source=self.test_ds,
        )
        self.assertEqual(order_ids, [6, 7, 8, 9, 10])
        # 逐个提交交易信号并打印相关余额的变化, 重复提交信号不会成功，只会返回None
        self.assertIsNone(submit_order(1, data_source=self.test_ds))
        self.assertEqual(submit_order(6, data_source=self.test_ds), 6)
        self.assertEqual(submit_order(7, data_source=self.test_ds), 7)
        self.assertEqual(submit_order(9, data_source=self.test_ds), 9)

        # signal 7 is filled with 100 shares sold at 90.0, with transaction fee 5.5
        raw_trade_result = {
            'order_id':        7,
            'filled_qty':      100.0,
            'price':           90.0,
            'transaction_fee': 5.5,
            'canceled_qty':    0.0,
        }
        print(f'\n------------START PROCESS TRADE RESULT-----------------\n'
              f'before processing trade result 7, trade signal: \n'
              f'{read_trade_order_detail(7, data_source=self.test_ds)}\n')
        process_account_delivery(account_id=1, data_source=self.test_ds, config=delivery_config)
        process_trade_result(raw_trade_result, data_source=self.test_ds)
        print(f'after processing trade result 7, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}\n'
              f'trade_signal_detail of order_id == 7: \n'
              f'{read_trade_order_detail(7, data_source=self.test_ds)}\n'
              f'trade_result_detail of order_id == 7: \n'
              f'{read_trade_results_by_order_id(7, data_source=self.test_ds).loc[5].to_dict()}')
        trade_result = read_trade_result_by_id(5, data_source=self.test_ds)
        # check cash availability
        own_cash, available_cash, total_invest = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertEqual(own_cash,
                         100000.0 - 100 * 60.5 - 5.0 - 100 * 81.0 - 12.5 - 400 * 89.5 - 7.5 + 100 * 90.0 - 5.5)
        self.assertEqual(available_cash, 100000.0 - 100 * 60.5 - 5.0 - 100 * 81.0 - 12.5 - 400 * 89.5 - 7.5)
        self.assertAlmostEqual(total_invest, 100000.0)
        trade_signal_detail = read_trade_order_detail(7, data_source=self.test_ds)
        # check available qty availability
        symbols, own_qty, available_qty, costs = get_account_position_availabilities(
                1,
                trade_signal_detail['symbol'],
                data_source=self.test_ds,
        )
        self.assertEqual(int(own_qty), 100.0 - 100.0)
        self.assertEqual(int(available_qty), 100.0 - 100.0)
        self.assertEqual(float(costs), 0)  # 因为没有持仓，所以costs为0
        # check trade_signal status
        self.assertEqual(trade_signal_detail['status'], 'filled')
        # check trade result status
        self.assertEqual(trade_result['delivery_amount'], 8994.5)
        self.assertEqual(trade_result['delivery_status'], 'ND')
        # check trade result summary with no share
        summary = get_last_trade_result_summary(1, data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with no shares: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB'])
        self.assertEqual(list(summary[1]), [-100, 0, 100, 400, 0])
        self.assertEqual(list(summary[2]), [90, 0, 81, 89.5, 0])
        # check trade result summary with share
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'AMZN'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'AMZN'])
        self.assertEqual(list(summary[1]), [0, -100, 400])
        self.assertEqual(list(summary[2]), [0, 90, 89.5])
        # check trade result summary with share that out of range
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'MSFT', 'FB'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "MSFT", "FB"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'MSFT', 'FB'])
        self.assertEqual(list(summary[1]), [0, -100, 100, 0])
        self.assertEqual(list(summary[2]), [0, 90, 81, 0])

        # signal 9 is partially filled with 300 shares sold at 140.0, with transaction fee 65.3
        raw_trade_result = {
            'order_id':        9,
            'filled_qty':      300.0,
            'price':           140.0,
            'transaction_fee': 65.3,
            'canceled_qty':    0.0,
        }
        print(f'\n------------START PROCESS TRADE RESULT-----------------\n'
              f'before processing trade result 9, trade signal: \n'
              f'{read_trade_order_detail(9, data_source=self.test_ds)}\n')
        process_account_delivery(account_id=1, data_source=self.test_ds, config=delivery_config)
        process_trade_result(raw_trade_result, data_source=self.test_ds)
        print(f'after processing trade result 9, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}\n'
              f'trade_signal_detail of order_id == 9: \n'
              f'{read_trade_order_detail(9, data_source=self.test_ds)}\n'
              f'trade_result_detail of order_id == 9: \n'
              f'{read_trade_results_by_order_id(9, data_source=self.test_ds).loc[6].to_dict()}')
        trade_result = read_trade_result_by_id(6, data_source=self.test_ds)
        # check cash availability
        own_cash, available_cash, total_invest = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertAlmostEqual(own_cash, 50025 + 100 * 90.0 - 5.5 + 300 * 140.0 - 65.3)
        self.assertAlmostEqual(available_cash, 50025 + 100 * 90.0 - 5.5)
        self.assertAlmostEqual(total_invest, 100000.0)
        trade_signal_detail = read_trade_order_detail(9, data_source=self.test_ds)
        # check available qty availability
        symbols, own_qty, available_qty, costs = get_account_position_availabilities(
                1,
                trade_signal_detail['symbol'],
                data_source=self.test_ds,
        )
        self.assertEqual(int(own_qty), 400.0 - 300.0)
        self.assertEqual(int(available_qty), 400.0 - 300.0)
        self.assertEqual(float(costs), (89.51875 * 400 + 65.3 - 300.0 * 140) / 100)
        # check trade_signal status
        self.assertEqual(trade_signal_detail['status'], 'partial-filled')
        # check trade result status
        self.assertEqual(trade_result['delivery_amount'], 41934.7)
        self.assertEqual(trade_result['delivery_status'], 'ND')
        # check trade result summary with no share
        summary = get_last_trade_result_summary(1, data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with no shares: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB'])
        self.assertEqual(list(summary[1]), [-100, 0, 100, -300, 0])
        self.assertEqual(list(summary[2]), [90, 0, 81, 140, 0])
        # check trade result summary with share
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'AMZN'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'AMZN'])
        self.assertEqual(list(summary[1]), [0, -100, -300])
        self.assertEqual(list(summary[2]), [0, 90, 140])
        # check trade result summary with share that out of range
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'MSFT', 'FB'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "MSFT", "FB"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'MSFT', 'FB'])
        self.assertEqual(list(summary[1]), [0, -100, 100, 0])
        self.assertEqual(list(summary[2]), [0, 90, 81, 0])

        # partially filled order 9 with 99 shares sold at 191.0, with transaction fee 23.9
        raw_trade_result = {
            'order_id':        9,
            'filled_qty':      99.0,
            'price':           191.0,
            'transaction_fee': 23.9,
            'canceled_qty':    0.0,
        }
        process_account_delivery(account_id=1, data_source=self.test_ds, config=delivery_config)
        process_trade_result(raw_trade_result, data_source=self.test_ds)
        print(f'after processing trade result 9, position data of account_id == 1: \n'
              f'{get_account_positions(1, data_source=self.test_ds)}\n'
              f'cash availability of account_id == 1: \n'
              f'{get_account_cash_availabilities(1, data_source=self.test_ds)}\n'
              f'trade_signal_detail of order_id == 9: \n'
              f'{read_trade_order_detail(9, data_source=self.test_ds)}\n'
              f'trade_result_detail of order_id == 9: \n'
              f'{read_trade_results_by_order_id(9, data_source=self.test_ds).loc[7].to_dict()}')
        # check cash availability
        own_cash, available_cash, total_invest = get_account_cash_availabilities(1, data_source=self.test_ds)
        self.assertAlmostEqual(own_cash, 50025 + 100 * 90.0 - 5.5 + 300 * 140.0 - 65.3 + 99 * 191.0 - 23.9)
        self.assertAlmostEqual(available_cash, 50025 + 100 * 90.0 - 5.5 + 300 * 140.0 - 65.3)
        self.assertAlmostEqual(total_invest, 100000.0)
        trade_signal_detail = read_trade_order_detail(9, data_source=self.test_ds)
        # check available qty availability
        symbols, own_qty, available_qty, costs = get_account_position_availabilities(
                1,
                trade_signal_detail['symbol'],
                data_source=self.test_ds,
        )
        self.assertEqual(int(own_qty), 400.0 - 300.0 - 99.0)
        self.assertEqual(int(available_qty), 400.0 - 300.0 - 99.0)
        self.assertAlmostEqual(float(costs), (-61.272 * 100 - 99 * 191 + 23.9) / 1.0)
        # check trade_signal status
        self.assertEqual(trade_signal_detail['status'], 'partial-filled')
        # check trade result status
        trade_result = read_trade_result_by_id(6, data_source=self.test_ds)
        self.assertEqual(trade_result['delivery_amount'], 41934.7)
        self.assertEqual(trade_result['delivery_status'], 'DL')
        trade_result = read_trade_result_by_id(7, data_source=self.test_ds)
        self.assertEqual(trade_result['delivery_amount'], 18885.1)
        self.assertEqual(trade_result['delivery_status'], 'ND')

        # process trade result delivery for the last order
        process_account_delivery(account_id=1, data_source=self.test_ds, config=delivery_config)
        # check available qty availability
        symbols, own_qty, available_qty, costs = get_account_position_availabilities(
                1,
                trade_signal_detail['symbol'],
                data_source=self.test_ds,
        )
        self.assertEqual(int(own_qty), 400.0 - 300.0 - 99.0)
        self.assertEqual(int(available_qty), 400.0 - 300.0 - 99.0)
        self.assertAlmostEqual(float(costs), -25012.3)
        # check trade_signal status
        self.assertEqual(trade_signal_detail['status'], 'partial-filled')
        # check trade result status
        trade_result = read_trade_result_by_id(6, data_source=self.test_ds)
        self.assertEqual(trade_result['delivery_amount'], 41934.7)
        self.assertEqual(trade_result['delivery_status'], 'DL')
        trade_result = read_trade_result_by_id(7, data_source=self.test_ds)
        self.assertEqual(trade_result['delivery_amount'], 18885.1)
        self.assertEqual(trade_result['delivery_status'], 'DL')
        # check trade result summary with no share
        # in the summary, filled amount will be total amount in order, and price will be average filled price
        summary = get_last_trade_result_summary(1, data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with no shares: \n{summary}')
        self.assertEqual(summary[0], ['GOOG', 'APPL', 'MSFT', 'AMZN', 'FB'])
        self.assertEqual(list(summary[1]), [-100, 0, 100, -399, 0])
        self.assertEqual(list(summary[2]), [90, 0, 81, 165.5, 0])
        # check trade result summary with share
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'AMZN'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "AMZN"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'AMZN'])
        self.assertEqual(list(summary[1]), [0, -100, -399])
        self.assertEqual(list(summary[2]), [0, 90, 165.5])
        # check trade result summary with share that out of range
        summary = get_last_trade_result_summary(1, shares=['APPL', 'GOOG', 'MSFT', 'FB'], data_source=self.test_ds)
        print(f'last trade result summary of account_id == 1 with shares ["GOOG", "APPL", "MSFT", "FB"]: \n{summary}')
        self.assertEqual(summary[0], ['APPL', 'GOOG', 'MSFT', 'FB'])
        self.assertEqual(list(summary[1]), [0, -100, 100, 0])
        self.assertEqual(list(summary[2]), [0, 90, 81, 0])

    def test_cancel_orders(self):
        """ test cancel_orders function """
        # TODO: implement this function to test if partial-filled orders can be partially cancelled
        #  and unfilled orders can be fully cancelled
        pass

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
            'PT_buy_threshold':  0.0,
            'PT_sell_threshold': 0.0,
            'allow_sell_short':  True,
            'trade_batch_size':  100.,
            'sell_batch_size':   1.,
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
            'PT_buy_threshold':  0.1,
            'PT_sell_threshold': -0.1,
            'allow_sell_short':  False,
            'trade_batch_size':  0.,
            'sell_batch_size':   0.,
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
        # test _signal_to_order_elements with only one symbol, buy 500 shares in long position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([5000.0])
        amounts_to_sell = np.array([0.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
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
        self.assertEqual(quoted_prices, [10.0])
        self.assertEqual(messages, [''])
        available_cash = 10000.0
        available_amounts = np.array([1000.0])

        # test _signal_to_order_elements with only one symbol, sell 500 shares in long position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([-500.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
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
        self.assertEqual(quoted_prices, [10.0])
        self.assertEqual(messages, [''])

        # test _signal_to_order_elements with only one symbol, sell 500 shares in short position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([500.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
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
        self.assertEqual(quoted_prices, [10.0])
        self.assertEqual(messages, [''])

        # test _signal_to_order_elements with only one symbol, buy 500 shares in short position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([-5000.0])
        amounts_to_sell = np.array([0.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
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
        self.assertEqual(quoted_prices, [10.0])
        self.assertEqual(messages, [''])

        # test _signal_to_order_elements with only one symbol, sell 1000 shares while only 700 shares available
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([-1000.0])
        available_cash = 10000.0
        available_amounts = np.array([700.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
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
        self.assertEqual(quoted_prices, [10.0, 10.0])
        self.assertEqual(messages, ['Not enough available stock(700.0), '
                                    'sell qty (-1000.0) reduced and rounded to 700.0',
                                    'Allow sell short, continue to buy short positions 300.0'])

        # test _signal_to_order_elements with only one symbol,
        # sell 1000 short shares while only 500 short shares available
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([1000.0])
        available_cash = 10000.0
        available_amounts = np.array([-700.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
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
        self.assertEqual(quoted_prices, [10.0, 10.0])
        self.assertEqual(messages, ['Not enough short position stock (700.0), '
                                    'sell short qty (1000.0) reduced and rounded to 700.0',
                                    'Allow sell short, continue to buy long positions 300.0'])

        # test _signal_to_order_elements with only one symbol, buy shares with not enough cash
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([10000.0])
        amounts_to_sell = np.array([0.0])
        available_cash = 5000.0
        available_amounts = np.array([1000.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
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
        self.assertEqual(quoted_prices, [10.0])
        self.assertEqual(messages, ['Not enough available cash (5000.000), adjusted cash to spend to 50.0%'])

        # test _signal_to_order_elements with multiple symbols
        shares = ['000001', '000002', '000003', '000004', '000005', '000006']
        prices = np.array([10., 10., 10., 10., 10., 10.])
        cash_to_spend = np.array([5000.0, 0.0, 0.0, 3500.0, -1000.0, 0.0])
        amounts_to_sell = np.array([0.0, 0.0, 500.0, 150.0, 0.0, 500.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 1000.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
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
        self.assertEqual(quoted_prices, [10.0, 10.0, 10.0, 10.0, 10.0, 10.0])
        self.assertEqual(messages, ['', '', '', '', '', ''])

        # test _signal_to_order_elements with multiple symbols, with buy and sell moq = 0.0
        shares = ['000001', '000002', '000003', '000004', '000005', '000006']
        prices = np.array([10., 10., 10., 10., 10., 10.])
        cash_to_spend = np.array([5050.0, 0.0, 0.0, 3524.0, -1001.0, 0.0])
        amounts_to_sell = np.array([0.0, 0.0, 525.0, 153.8, 0.0, 500.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 650.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
                moq_buy=0.0,
                moq_sell=0.0,
                allow_sell_short=True,
        )
        self.assertEqual(symbols, ['000001', '000003', '000004', '000004', '000005', '000006'])
        self.assertEqual(positions, ['long', 'short', 'long', 'short', 'short', 'short'])
        self.assertEqual(directions, ['buy', 'sell', 'buy', 'sell', 'buy', 'sell'])
        self.assertEqual(quantities, [505.0, 525.0, 352.4, 153.8, 100.1, 500.0])
        self.assertEqual(quoted_prices, [10.0, 10.0, 10.0, 10.0, 10.0, 10.0])
        self.assertEqual(messages, ['', '', '', '', '', ''])

        # test _signal_to_order_elements with multiple symbols, with buy moq = 100 and sell moq = 10.0
        shares = ['000001', '000002', '000003', '000004', '000005', '000006']
        prices = np.array([10., 10., 10., 10., 10., 10.])
        cash_to_spend = np.array([5050.0, 0.0, 0.0, 3524.0, -1001.0, 0.0])
        amounts_to_sell = np.array([0.0, 0.0, 525.0, 153.8, 0.0, 500.0])
        available_cash = 10000.0
        available_amounts = np.array([1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 650.0])

        symbols, positions, directions, quantities, quoted_prices, messages = _signal_to_order_elements(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices,
                available_cash=available_cash,
                available_amounts=available_amounts,
                moq_buy=100.0,
                moq_sell=10.0,
                allow_sell_short=True,
        )
        self.assertEqual(symbols, ['000001', '000003', '000004', '000004', '000005', '000006'])
        self.assertEqual(positions, ['long', 'short', 'long', 'short', 'short', 'short'])
        self.assertEqual(directions, ['buy', 'sell', 'buy', 'sell', 'buy', 'sell'])
        self.assertEqual(quantities, [500.0, 520.0, 300.0, 150.0, 100.0, 500.0])
        self.assertEqual(quoted_prices, [10.0, 10.0, 10.0, 10.0, 10.0, 10.0])
        self.assertEqual(messages, ['', '', '', '', '', ''])

    def test_parse_pt_signals(self):
        """ test parsing trade signal from pt_type signal"""
        # test parsing pt buy long signal with only one symbol
        signals = np.array([1])
        prices = np.array([10.])
        own_amounts = np.array([0.0])
        own_cash = 5000.0
        pt_buy_threshold = 0.5
        pt_sell_threshold = 0.5

        cash_to_spend, amounts_to_sell = _parse_pt_signals(
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

        cash_to_spend, amounts_to_sell = _parse_pt_signals(
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

        cash_to_spend, amounts_to_sell = _parse_pt_signals(
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

        cash_to_spend, amounts_to_sell = _parse_pt_signals(
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

        cash_to_spend, amounts_to_sell = _parse_pt_signals(
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
        """ test _parse_ps_signals function """
        # test parsing ps buy long signal with only one symbol
        signals = np.array([1])
        prices = np.array([10.])
        own_amounts = np.array([0.0])
        own_cash = 5000.0

        cash_to_spend, amounts_to_sell = _parse_ps_signals(
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

        cash_to_spend, amounts_to_sell = _parse_ps_signals(
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

        cash_to_spend, amounts_to_sell = _parse_ps_signals(
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

        cash_to_spend, amounts_to_sell = _parse_ps_signals(
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

        cash_to_spend, amounts_to_sell = _parse_ps_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                allow_sell_short=True
        )
        self.assertEqual(list(cash_to_spend), [1500.0, 0.0, 0.0, 0.0, -1500.0, 0.0])
        self.assertEqual(list(amounts_to_sell), [0.0, 0.0, -500.0, 0.0, 0.0, 250.0])

    def test_parse_vs_signals(self):
        """ test _parse_vs_signals function """
        # test parsing vs buy long signal with only one symbol
        signals = np.array([500])
        prices = np.array([10.])
        own_amounts = np.array([0.0])

        cash_to_spend, amounts_to_sell = _parse_vs_signals(
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

        cash_to_spend, amounts_to_sell = _parse_vs_signals(
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

        cash_to_spend, amounts_to_sell = _parse_vs_signals(
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

        cash_to_spend, amounts_to_sell = _parse_vs_signals(
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

        cash_to_spend, amounts_to_sell = _parse_vs_signals(
                signals=signals,
                prices=prices,
                own_amounts=own_amounts,
                allow_sell_short=True
        )
        self.assertEqual(list(cash_to_spend), [5000.0, 0.0, 0.0, -2500.0, 0.0, 0.0])
        self.assertEqual(list(amounts_to_sell), [0.0, 0.0, -500.0, 0.0, 0.0, 250.0])

    def test_get_symbol_names(self):
        """ test function get_symbol_names """

        for table in ['stock_basic', 'index_basic', 'fund_basic', 'future_basic', 'opt_basic']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)

        stock_basic_df = pd.DataFrame({
            'ts_code':     ['000001.SZ', '000002.SZ', '000004.SZ', '600251.SH', '000006.SZ', '000008.SZ'],
            'symbol':      ['000001', '000002', '000004', '600251', '000006', '000008'],
            'name':        ['平安银行', '万科A', '国华网安', '冠农股份', '深振业A', '神州高铁'],
            'area':        ['深圳', '深圳', '深圳', '深圳', '深圳', '深圳'],
            'industry':    ['银行', '全国地产', '软件服务', '农药化肥', '区域地产', '其他商业'],
            'full_name':   ['平安银行', '万科A', '国华网安', '冠农股份', '深振业A', '神州高铁'],
            'en_name':     ['Ping An Bank', 'Vanke A', 'Guohua Network Security', 'Guannong Shares',
                            'Shenzhen Zhenye A', 'Shenzhou High Speed Railway'],
            'cnspell':     ['PAYH', 'WK', 'GHWA', 'GN', 'SZYA', 'SZGJ'],
            'market':      ['主板', '主板', '主板', '主板', '主板', '主板'],
            'exchange':    ['SZSE', 'SZSE', 'SZSE', 'SSE', 'SZSE', 'SZSE'],
            'curr_type':   ['CNY', 'CNY', 'CNY', 'CNY', 'CNY', 'CNY'],
            'list_status': ['L', 'L', 'L', 'L', 'L', 'L'],
            'list_date':   ['19910403', '19910129', '19910114', '19901210', '19920427', '19910625'],
            'delist_date': ['22001231', '22001231', '22001231', '22001231', '22001231', '22001231'],
            'is_hs':       ['N', 'N', 'N', 'N', 'N', 'N'],
        })
        # stock_basic = self.test_ds.fetch_history_table_data(
        #         table='stock_basic',
        #         channel='df',
        #         df=stock_basic_df,
        # )
        self.test_ds.update_table_data('stock_basic', stock_basic_df)

        index_basic_df = pd.DataFrame({
            'ts_code':     ['000001.SH', '000002.SH', '000004.SH', '000006.SH', '000008.SH'],
            'name':        ['上证指数', 'A股指数', '工业指数', '地产指数', '综合指数'],
            'fullname':    ['上证指数', 'A股指数', '工业指数', '地产指数', '综合指数'],
            'market':      ['上证', '上证', '上证', '上证', '上证'],
            'publisher':   ['上证', '上证', '上证', '上证', '上证'],
            'index_type':  ['1', '1', '1', '1', '1'],
            'category':    ['1', '1', '1', '1', '1'],
            'base_date':   ['19901219', '19910129', '19910114', '19910129', '19910114'],
            'base_point':  ['100.0', '100.0', '100.0', '100.0', '100.0'],
            'list_date':   ['19910403', '19910129', '19910114', '19910129', '19910114'],
            'weight_rule': ['等权', '等权', '等权', '等权', '等权'],
            'desc':        ['描述', '描述', '描述', '描述', '描述'],
            'exp_date':    ['22001231', '22001231', '22001231', '22001231', '22001231'],
        })
        # index_basic = self.test_ds.fetch_history_table_data(
        #         table='index_basic',
        #         channel='df',
        #         df=index_basic_df,
        # )
        self.test_ds.update_table_data('index_basic', index_basic_df)

        # test get_symbol_names with only stock symbols
        print('test get_symbol_names with only stock symbols')
        symbol_names = get_symbol_names(
                self.test_ds,
                ['000001.SZ', '000002.SZ', '000004.SZ', '600251.SH', '000006.SZ', '000008.SZ']
        )
        print(symbol_names)
        self.assertEqual(symbol_names, ['平安银行', '万科A', '国华网安', '冠农股份', '深振业A', '神州高铁'])

        # test get_symbol_names with repeated symbols
        print('test get_symbol_names with repeated symbols')
        symbol_names = get_symbol_names(
                self.test_ds,
                ['000001.SZ', '000001.SZ', '000001.SZ', '600251.SH', '600251.SH', '600251.SH']
        )
        print(symbol_names)
        self.assertEqual(symbol_names, ['平安银行', '平安银行', '平安银行', '冠农股份', '冠农股份', '冠农股份'])

        # test get_symbol_names with stock and index mixed symbols
        print('test get_symbol_names with stock and index mixed symbols')
        symbol_names = get_symbol_names(
                self.test_ds,
                ['000001.SZ', '000002.SZ', '000004.SZ', '000001.SH', '000002.SH', '000004.SH',
                 '600251.SH', '000006.SZ', '000008.SZ', '600251.SH', '000006.SH', '000008.SH']
        )
        print(symbol_names)
        self.assertEqual(symbol_names, ['平安银行', '万科A', '国华网安', '上证指数', 'A股指数', '工业指数',
                                        '冠农股份', '深振业A', '神州高铁', '冠农股份', '地产指数', '综合指数'])

        # "N/A" will be returned for symbols not found or not a symbol
        print('test get_symbol_names with symbols not found or not a symbol')
        symbol_names = get_symbol_names(
                self.test_ds,
                ['000001.SZ', '000002.SZ', '000000.SZ', 'Not_symbol']
        )
        print(symbol_names)
        self.assertEqual(symbol_names, ['平安银行', '万科A', 'N/A', 'N/A'])

        # "N/A" will be returned for symbols whose basic data is not downloaded, at this moment, fund symbols
        print('test get_symbol_names with symbols whose basic data is not downloaded')
        symbol_names = get_symbol_names(
                self.test_ds,
                ['000001.SZ', '000002.SZ', '000001.OF', '000002.OF']
        )
        print(symbol_names)
        self.assertEqual(symbol_names, ['平安银行', '万科A', 'N/A', 'N/A'])

        # download func basic data and names will be returned after refresh
        print('test get_symbol_names with symbols whose basic data is now downloaded but not refreshed')

        fund_basic_df = pd.DataFrame({
            'ts_code':       ['000606.OF', '000291.OF'],
            'name':          ['天弘优选', '鹏华普悦'],
            'management':    ['天弘基金', '鹏华基金'],
            'custodian':     ['中国银行', '中国银行'],
            'fund_type':     ['股票型', '股票型'],
            'found_date':    ['20150130', '20150130'],
            'due_date':      ['22001231', '22001231'],
            'list_date':     ['20150130', '20150130'],
            'issue_date':    ['20150130', '20150130'],
            'delist_date':   ['22001231', '22001231'],
            'issue_amount':  ['1000000000.0', '1000000000.0'],
            'm_fee':         ['0.1', '0.1'],
            'c_fee':         ['0.1', '0.1'],
            'duration_year': ['3.0', '3.0'],
            'p_value':       ['1.0', '1.0'],
            'min_amount':    ['100.0', '100.0'],
            'exp_return':    ['0.1', '0.1'],
            'benchmark':     ['沪深300', '沪深300'],
            'status':        ['在售', '在售'],
            'invest_type':   ['股票型', '股票型'],
            'type':          ['开放式', '开放式'],
        })
        # fund_basic = self.test_ds.fetch_history_table_data(
        #         table='fund_basic',
        #         channel='df',
        #         df=fund_basic_df,
        # )
        self.test_ds.update_table_data('fund_basic', fund_basic_df)

        print(symbol_names)
        symbol_names = get_symbol_names(
                self.test_ds,
                ['000001.SZ', '000002.SZ', '000606.OF', '000291.OF']
        )
        self.assertEqual(symbol_names, ['平安银行', '万科A', 'N/A', 'N/A'])
        print('after refresh the names are returned')
        symbol_names = get_symbol_names(
                self.test_ds,
                ['000001.SZ', '000002.SZ', '000606.OF', '000291.OF'],
                refresh=True,
        )
        print(symbol_names)
        self.assertEqual(symbol_names, ['平安银行', '万科A', '天弘优选', '鹏华普悦'])

    def test_calculate_cost_change(self):
        """ test function calculate_cost_change"""
        cost_change, new_cost = calculate_cost_change(
                prev_qty=100.0,
                prev_unit_cost=10.0,
                qty_change=100.0,
                price=12.0,
                transaction_fee=0.0,
        )
        self.assertAlmostEqual(cost_change, 1.)
        self.assertAlmostEqual(new_cost, 11.)

        cost_change, new_cost = calculate_cost_change(
                prev_qty=100.0,
                prev_unit_cost=10.0,
                qty_change=100.0,
                price=12.0,
                transaction_fee=200.0,
        )
        self.assertAlmostEqual(cost_change, 2.)
        self.assertAlmostEqual(new_cost, 12.)

        cost_change, new_cost = calculate_cost_change(
                prev_qty=200.0,
                prev_unit_cost=10.0,
                qty_change=-100.0,
                price=12.0,
                transaction_fee=0.0,
        )
        self.assertAlmostEqual(cost_change, -2.)
        self.assertAlmostEqual(new_cost, 8.)

        cost_change, new_cost = calculate_cost_change(
                prev_qty=200.0,
                prev_unit_cost=10.0,
                qty_change=-100.0,
                price=30.0,
                transaction_fee=0.0,
        )
        self.assertAlmostEqual(cost_change, -20.)
        self.assertAlmostEqual(new_cost, -10.)

        cost_change, new_cost = calculate_cost_change(
                prev_qty=200.0,
                prev_unit_cost=10.0,
                qty_change=-100.0,
                price=30.0,
                transaction_fee=100.0,
        )
        self.assertAlmostEqual(cost_change, -19.)
        self.assertAlmostEqual(new_cost, -9.)

        cost_change, new_cost = calculate_cost_change(
                prev_qty=200.0,
                prev_unit_cost=10.0,
                qty_change=-200.0,
                price=30.0,
                transaction_fee=100.0,
        )
        self.assertAlmostEqual(cost_change, -10.)
        self.assertAlmostEqual(new_cost, -0.)


if __name__ == '__main__':
    unittest.main()