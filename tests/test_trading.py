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
from qteasy.trading import generate_signal, submit_signal
from qteasy.trading import new_account, get_account, update_account, update_account_balance, get_or_create_position
from qteasy.trading import update_position, get_account_positions, check_account_availability
from qteasy.trading import check_position_availability, record_trade_signal, update_trade_signal, read_trade_signal
from qteasy.trading import query_trade_signals, submit_signal, output_trade_signal


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
        position = get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        self.assertIsInstance(position, dict)
        print(position)
        self.assertEqual(position['account_id'], 1)
        self.assertEqual(position['symbol'], 'AAPL')
        self.assertEqual(position['position'], 'long')
        self.assertEqual(position['qty'], 0)
        position = get_or_create_position(1, 'AAPL', 'short', data_source=self.test_ds)
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
        position = get_or_create_position(1, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(position['qty'], 100)
        self.assertEqual(position['available_qty'], 0)
        position = get_or_create_position(1, 'AAPL', 'short', data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 0)
        # update qty and available qty in the same time
        update_position(3, data_source=self.test_ds, qty_change=200, available_qty_change=100)
        update_position(4, data_source=self.test_ds, qty_change=300, available_qty_change=300)
        # check updated positions
        position = get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(position['qty'], 200)
        self.assertEqual(position['available_qty'], 100)
        position = get_or_create_position(2, 'AAPL', 'short', data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 300)
        # update qty and available qty on previous positions
        update_position(3, data_source=self.test_ds, qty_change=100, available_qty_change=-100)
        update_position(4, data_source=self.test_ds, qty_change=300, available_qty_change=100)
        # check updated positions
        position = get_or_create_position(2, 'AAPL', 'long', data_source=self.test_ds)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 0)
        position = get_or_create_position(2, 'AAPL', 'short', data_source=self.test_ds)
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

    def test_check_account_availability(self):
        """ test check_account_availability function """
        pass

    # test foundational functions related to signal generation and submission

    def test_record_and_read_signal(self):
        """ test record_and_read_signal function """
        pass

    def test_update_trade_signal(self):
        """ test update_trade_signal function """
        pass

    def test_query_trade_signals(self):
        """ test query_trade_signals function """
        pass

    # test sub functions related to signal generation and submission
    def test_parse_signal(self):
        """ test submit_signal function """
        # test function submit_signal with only one symbol
        test_signal = {
            'account_id': 1,
            'pos_id': 1,
            'direction': 'buy',
            'order_type': 'market',
            'qty': 100,
            'price': 10.0,
            'submitted_time': None,
            'status': 'created',
        }

    def test_itemize_trade_signals(self):
        """ test itemize trade signals"""
        # test itemize_trade_signals with only one symbol, buy 500 shares in long position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([5000.0])
        amounts_to_sell = np.array([0.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices
        )
        self.assertEqual(symbols, ['000001'])
        self.assertEqual(positions, ['long'])
        self.assertEqual(directions, ['buy'])
        self.assertEqual(quantities, [500.0])

        # test itemize_trade_signals with only one symbol, sell 500 shares in long position
        shares = ['000001']
        prices = np.array([10.])
        cash_to_spend = np.array([0.0])
        amounts_to_sell = np.array([-500.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices
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

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices
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

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices
        )
        self.assertEqual(symbols, ['000001'])
        self.assertEqual(positions, ['short'])
        self.assertEqual(directions, ['buy'])
        self.assertEqual(quantities, [500.0])

        # test itemize_trade_signals with multiple symbols
        shares = ['000001', '000002', '000003', '000004', '000005', '000006']
        prices = np.array([10., 10., 10., 10., 10., 10.])
        cash_to_spend = np.array([5000.0, 0.0, 0.0, 3500.0, -1000.0, 0.0])
        amounts_to_sell = np.array([0.0, 0.0, 500.0, 150.0, 0.0, 500.0])

        symbols, positions, directions, quantities = itemize_trade_signals(
                shares=shares,
                cash_to_spend=cash_to_spend,
                amounts_to_sell=amounts_to_sell,
                prices=prices
        )
        self.assertEqual(symbols, ['000001', '000003', '000004', '000004', '000005', '000006'])
        self.assertEqual(positions, ['long', 'short', 'long', 'short', 'short', 'short'])
        self.assertEqual(directions, ['buy', 'sell', 'buy', 'sell', 'buy', 'sell'])
        self.assertEqual(quantities, [500.0, 500.0, 350.0, 150.0, 100.0, 500.0])

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
