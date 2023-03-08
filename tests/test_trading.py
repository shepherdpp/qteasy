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


class TestLiveTrade(unittest.TestCase):

    def setUp(self) -> None:
        """ execute before each test"""
        from qteasy import QT_ROOT_PATH
        self.qt_root_path = QT_ROOT_PATH
        self.data_test_dir = 'data_test/'
        # 测试数据不会放在默认的data路径下，以免与已有的文件混淆
        # 使用测试数据库进行与database型数据源的测试
        config = qt.QT_CONFIG
        self.ds_db = DataSource('db',
                                host=config['test_db_host'],
                                user=config['test_db_user'],
                                password=config['test_db_password'],
                                db_name=config['test_db_name'])
        self.ds_csv = DataSource('file', file_type='csv', file_loc=self.data_test_dir)
        self.ds_hdf = DataSource('file', file_type='hdf', file_loc=self.data_test_dir)
        self.ds_fth = DataSource('file', file_type='fth', file_loc=self.data_test_dir)

    # test foundational functions related to database info read and write
    def test_create_and_get_account(self):
        """ test new_account function """
        # test new_account with simple account info
        user_name = 'test_user'
        cash_amount = 10000.0
        account_id = new_account(user_name, cash_amount)
        print(f'account created, id: {account_id}')

    def test_update_account(self):
        """ test update_account function """
        pass

    def test_create_and_get_position(self):
        """ test new_position function """
        pass

    def test_update_position(self):
        """ test update_position function """
        # test update_position with only one symbol
        pass

    def test_check_account_availability(self):
        """ test check_account_availability function """
        pass

    # test foundational functions related to signal generation and submission

    def test_record_and_read_signal(self):
        """ test record_and_read_signal function """
        # test recording and reading signal
        signal = np.array([1, 2, 3, 4, 5])
        record_signal(signal, 'test_signal')
        read_signal = read_trade_signal('test_signal')
        self.assertEqual(list(signal), list(read_signal))

        # test recording and reading signal with multiple symbols
        signal = np.array([[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]])
        record_signal(signal, 'test_signal')
        read_signal = read_signal('test_signal')
        self.assertEqual(list(signal[0]), list(read_signal[0]))
        self.assertEqual(list(signal[1]), list(read_signal[1]))

        # test recording and reading signal with multiple symbols and multiple time steps
        signal = np.array([[[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]], [[11, 12, 13, 14, 15], [16, 17, 18, 19, 20]]])
        record_signal(signal, 'test_signal')
        read_signal = read_signal('test_signal')
        self.assertEqual(list(signal[0][0]), list(read_signal[0][0]))
        self.assertEqual(list(signal[0][1]), list(read_signal[0][1]))
        self.assertEqual(list(signal[1][0]), list(read_signal[1][0]))
        self.assertEqual(list(signal[1][1]), list(read_signal[1][1]))

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
        submit_signal(test_signal)

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
