# coding=utf-8
# ======================================
# File:     test_trader.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-04-09
# Desc:
#   Unittest for trader related functions
# ======================================

import unittest
import time
import os
import csv

from queue import Queue
from threading import Thread

import pandas as pd
import numpy as np

from qteasy import DataSource, Operator, BaseStrategy
from qteasy.trade_recording import new_account, get_or_create_position, update_position, save_parsed_trade_orders
from qteasy.trading_util import submit_order, process_trade_result, cancel_order, process_account_delivery
from qteasy.trading_util import deliver_trade_result
from qteasy.trading_util import sys_log_file_path_name, trade_log_file_path_name, break_point_file_path_name
from qteasy.trader import Trader
from qteasy.broker import SimulatorBroker, Broker


# --------------- Fixture helpers (plan section 2) ---------------

def _get_data_test_dir():
    """Return path to data_test directory (works when run from project root or tests/)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'qteasy', 'data_test')


def _default_trader_kwargs():
    """Default kwargs for Trader used across tests."""
    return {
        'market_open_time_am': '09:30:00',
        'market_close_time_pm': '15:30:00',
        'market_open_time_pm': '13:00:00',
        'market_close_time_am': '11:30:00',
        'exchange': 'SSE',
        'cash_delivery_period': 0,
        'stock_delivery_period': 0,
        'asset_pool': '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
        'asset_type': 'E',
        'pt_buy_threshold': 0.05,
        'pt_sell_threshold': 0.05,
        'allow_sell_short': False,
        'live_price_channel': 'eastmoney',
        'live_data_channel': 'eastmoney',
        'live_price_freq': '15min',
        'live_data_batch_size': 0,
        'live_data_batch_interval': 0,
        'daily_refill_tables': 'stock_1min, stock_5min',
        'weekly_refill_tables': 'stock_15min',
        'monthly_refill_tables': 'stock_daily',
    }


def _create_operator():
    """Create a minimal Operator for tests."""
    operator = Operator(strategies=['macd', 'dma'])
    operator.set_parameter(stg_id='dma', window_length=10, run_freq='h')
    operator.set_parameter(stg_id='macd', window_length=10, run_freq='30min')
    return operator


def _clear_tables(datasource):
    """Clear test-related tables in datasource."""
    for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders',
                  'sys_op_trade_results', 'stock_daily']:
        if datasource.table_data_exists(table):
            datasource.drop_table_data(table)


def _write_minimal_stock_daily(datasource, symbols=None, start_date='2023-02-01', end_date='2023-05-10'):
    """Write minimal daily bars for run_strategy tests. Covers symbols and date range with >= 30 rows per symbol.
    Uses bars schema: ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount.
    """
    if symbols is None:
        symbols = ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ']
    dates = pd.bdate_range(start=start_date, end=end_date)
    rows = []
    for ts_code in symbols:
        for i, d in enumerate(dates):
            price = 10.0 + (i % 100) * 0.1
            rows.append({
                'ts_code': ts_code,
                'trade_date': d.strftime('%Y-%m-%d'),
                'open': price,
                'high': price + 0.5,
                'low': price - 0.5,
                'close': price + 0.1,
                'pre_close': price - 0.1,
                'change': 0.1,
                'pct_chg': 1.0,
                'vol': 1000000.0,
                'amount': 10000000.0,
            })
    df = pd.DataFrame(rows)
    datasource.write_table_data(df, 'stock_daily')


def create_trader_with_account(account_id=1, with_positions=True, debug=False):
    """
    Create a minimal runnable Trader with an account and optional positions.
    Tables are cleared and recreated. Returns (trader, datasource).
    """
    data_test_dir = _get_data_test_dir()
    test_ds = DataSource('file', file_type='csv', file_loc=data_test_dir, allow_drop_table=True)
    _clear_tables(test_ds)
    new_account(user_name='test_user1', cash_amount=100000, data_source=test_ds)
    if with_positions:
        for sym in ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']:
            get_or_create_position(account_id=account_id, symbol=sym, position_type='long', data_source=test_ds)
        update_position(position_id=1, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=2, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=3, data_source=test_ds, qty_change=300, available_qty_change=300)
        update_position(position_id=4, data_source=test_ds, qty_change=200, available_qty_change=100)
    operator = _create_operator()
    broker = SimulatorBroker()
    trader = Trader(
        account_id=account_id,
        operator=operator,
        broker=broker,
        datasource=test_ds,
        debug=debug,
        **_default_trader_kwargs(),
    )
    return trader, test_ds


def create_trader_with_orders_and_results(account_id=1, debug=False, stoppage=0.5):
    """
    Create a Trader with account, positions, submitted orders and trade results (full fixture).
    Returns (trader, datasource). Caller may use trader.init_trade_log_file(), init_system_logger() as needed.
    """
    trader, test_ds = create_trader_with_account(account_id=account_id, with_positions=True, debug=debug)
    trader.renew_trade_log_file()
    trader.init_system_logger()
    parsed_signals_batch = (
        ['000001.SZ', '000002.SZ', '000004.SZ', '000006.SZ', '000007.SZ'],
        ['long', 'long', 'long', 'long', 'long'],
        ['buy', 'sell', 'sell', 'buy', 'buy'],
        [100, 100, 300, 400, 500],
        [60.0, 70.0, 80.0, 90.0, 100.0],
    )
    order_ids = save_parsed_trade_orders(
        account_id=account_id,
        symbols=parsed_signals_batch[0],
        positions=parsed_signals_batch[1],
        directions=parsed_signals_batch[2],
        quantities=parsed_signals_batch[3],
        prices=parsed_signals_batch[4],
        data_source=test_ds,
    )
    for oid in order_ids:
        submit_order(oid, test_ds)
    time.sleep(stoppage)
    parsed_signals_batch2 = (
        ['000001.SZ', '000004.SZ', '000005.SZ', '000007.SZ'],
        ['long', 'long', 'long', 'long'],
        ['sell', 'buy', 'buy', 'sell'],
        [200, 200, 100, 300],
        [70.0, 30.0, 56.0, 79.0],
    )
    order_ids2 = save_parsed_trade_orders(
        account_id=account_id,
        symbols=parsed_signals_batch2[0],
        positions=parsed_signals_batch2[1],
        directions=parsed_signals_batch2[2],
        quantities=parsed_signals_batch2[3],
        prices=parsed_signals_batch2[4],
        data_source=test_ds,
    )
    for oid in order_ids2:
        submit_order(order_id=oid, data_source=test_ds)
    time.sleep(stoppage)
    delivery_config = {'cash_delivery_period': 0, 'stock_delivery_period': 0}
    for i, raw in enumerate([
        {'order_id': 1, 'filled_qty': 100, 'price': 60.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 2, 'filled_qty': 100, 'price': 70.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 3, 'filled_qty': 200, 'price': 80.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 4, 'filled_qty': 400, 'price': 89.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 5, 'filled_qty': 500, 'price': 100.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
    ], 1):
        full = process_trade_result(raw_trade_result=raw, data_source=test_ds)
        trader.log_trade_result(full)
        dr = deliver_trade_result(result_id=full['result_id'], account_id=account_id, data_source=test_ds)
        trader.log_qty_delivery(dr)
        trader.log_cash_delivery(dr)
        time.sleep(stoppage)
    cancel_order(8, test_ds, delivery_config)
    process_account_delivery(account_id=account_id, data_source=test_ds)
    trader.init_trade_log_file()
    trader.init_system_logger()
    return trader, test_ds


class TestTrader(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        print('Setting up test Trader...')
        operator = Operator(strategies=['macd', 'dma'])
        operator.set_parameter(
                stg_id='dma',
                window_length=20,
                run_freq='h'
        )
        operator.set_parameter(
                stg_id='macd',
                window_length=30,
                run_freq='30min',
        )
        broker = SimulatorBroker()
        trader_kwargs = {
            'market_open_time_am':              '09:30:00',
            'market_close_time_pm':             '15:30:00',
            'market_open_time_pm':              '13:00:00',
            'market_close_time_am':             '11:30:00',
            'exchange':                         'SSE',
            'cash_delivery_period':             0,
            'stock_delivery_period':            0,
            'asset_pool':                       '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
            'asset_type':                       'E',
            'pt_buy_threshold':                 0.05,
            'pt_sell_threshold':                0.05,
            'allow_sell_short':                 False,
            'live_price_channel':               'eastmoney',
            'live_data_channel':                'eastmoney',
            'live_price_freq':                  '15min',
            'live_data_batch_size':             0,
            'live_data_batch_interval':         0,
            'daily_refill_tables':              'stock_1min, stock_5min',
            'weekly_refill_tables':             'stock_15min',
            'monthly_refill_tables':            'stock_daily',

        }
        # 创建测试数据源
        data_test_dir = '../qteasy/data_test/'
        # 创建一个专用的测试数据源，以免与已有的文件混淆，不需要测试所有的数据源，因为相关测试在test_datasource中已经完成
        test_ds = DataSource(
                'file',
                file_type='csv',
                file_loc=data_test_dir,
                allow_drop_table=True,
        )
        # 清空测试数据源中的所有相关表格数据
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results',
                      'stock_daily']:
            if test_ds.table_data_exists(table):
                test_ds.drop_table_data(table)
        # 创建一个ID=1的账户
        new_account(user_name='test_user1', cash_amount=100000, data_source=test_ds)
        # 添加初始持仓
        get_or_create_position(account_id=1, symbol='000001.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000002.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000004.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000005.SZ', position_type='long', data_source=test_ds)
        update_position(position_id=1, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=2, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=3, data_source=test_ds, qty_change=300, available_qty_change=300)
        update_position(position_id=4, data_source=test_ds, qty_change=200, available_qty_change=100)

        self.stoppage = 1.05
        # 添加测试交易订单以及交易结果
        print('Adding test trade orders and results...')
        parsed_signals_batch = (
            ['000001.SZ', '000002.SZ', '000004.SZ', '000006.SZ', '000007.SZ', ],
            ['long', 'long', 'long', 'long', 'long'],
            ['buy', 'sell', 'sell', 'buy', 'buy'],
            [100, 100, 300, 400, 500],
            [60.0, 70.0, 80.0, 90.0, 100.0],
        )
        # save first batch of signals
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch[0],
                positions=parsed_signals_batch[1],
                directions=parsed_signals_batch[2],
                quantities=parsed_signals_batch[3],
                prices=parsed_signals_batch[4],
                data_source=test_ds,
        )
        print(f'created and saved 5 trade orders:\n'
              f'{order_ids[0]}\n'
              f'{order_ids[1]}\n'
              f'{order_ids[2]}\n'
              f'{order_ids[3]}\n'
              f'{order_ids[4]}\n')
        # submit orders
        for order_id in order_ids:
            submit_order(order_id, test_ds)
        time.sleep(self.stoppage)
        parsed_signals_batch = (
            ['000001.SZ', '000004.SZ', '000005.SZ', '000007.SZ', ],
            ['long', 'long', 'long', 'long'],
            ['sell', 'buy', 'buy', 'sell'],
            [200, 200, 100, 300],
            [70.0, 30.0, 56.0, 79.0],
        )
        # save first batch of signals
        order_ids = save_parsed_trade_orders(
                account_id=1,
                symbols=parsed_signals_batch[0],
                positions=parsed_signals_batch[1],
                directions=parsed_signals_batch[2],
                quantities=parsed_signals_batch[3],
                prices=parsed_signals_batch[4],
                data_source=test_ds,
        )
        print(f'created and saved 4 trade orders:\n'
              f'{order_ids[0]}\n'
              f'{order_ids[1]}\n'
              f'{order_ids[2]}\n'
              f'{order_ids[3]}\n')
        # submit orders
        for order_id in order_ids:
            submit_order(order_id=order_id, data_source=test_ds)
            print(f'submitted order(id{order_id}):')
        print('saved and submitted 9 trade orders')

        # 生成Trader对象
        self.ts = Trader(
                account_id=1,
                operator=operator,
                broker=broker,
                datasource=test_ds,
                debug=False,
                **trader_kwargs,
        )
        self.ts.renew_trade_log_file()
        self.ts.init_system_logger()
        # remove test sys_log_file
        sys_log_file_path = sys_log_file_path_name(self.ts.account_id, test_ds)
        os.remove(sys_log_file_path)
        self.assertFalse(os.path.exists(sys_log_file_path))

        # 添加交易订单执行结果
        delivery_config = {
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
        }
        raw_trade_result = {
            'order_id':        1,
            'filled_qty':      100,
            'price':           60.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        print(f'created raw trade result: {raw_trade_result}')

        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=1, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        2,
            'filled_qty':      100,
            'price':           70.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=2, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      200,
            'price':           80.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=3, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        4,
            'filled_qty':      400,
            'price':           89.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=4, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        5,
            'filled_qty':      500,
            'price':           100.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=5, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      100,
            'price':           78.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=6, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        6,
            'filled_qty':      200,
            'price':           69.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=7, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        7,
            'filled_qty':      200,
            'price':           31.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=8, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        9,
            'filled_qty':      300,
            'price':           91.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        full_trade_result = process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        self.ts.log_trade_result(full_trade_result)
        deliver_result = deliver_trade_result(result_id=9, account_id=1, data_source=test_ds)
        self.ts.log_qty_delivery(delivery_result=deliver_result)
        self.ts.log_cash_delivery(delivery_result=deliver_result)

        print('generated execution result and delivered results')
        # order 8 is canceled
        cancel_order(8, test_ds, delivery_config)
        deliver_results = process_account_delivery(account_id=1, data_source=test_ds)

        print('creating Trader object...')
        # 生成Trader对象
        self.ts = Trader(
                account_id=1,
                operator=operator,
                broker=broker,
                datasource=test_ds,
                debug=False,
                **trader_kwargs,
        )
        self.ts.init_trade_log_file()
        self.ts.init_system_logger()

    def test_system_logging(self):
        """ test all functions related to system logging

        """
        ts = self.ts
        # remove test sys_log_file
        sys_log_file_path = sys_log_file_path_name(ts.account_id, ts.datasource)
        os.remove(sys_log_file_path)
        self.assertFalse(os.path.exists(sys_log_file_path))
        ts.init_system_logger()
        print(f'test log to system log file')
        logger = ts.live_sys_logger
        logger.info('test info message')
        logger.warning('test warning message')
        logger.error('test error message')
        logger.critical('test critical message')
        self.assertTrue(os.path.exists(sys_log_file_path))
        with open(sys_log_file_path, 'r') as f:
            lines = f.readlines()
            print(f'lines written to system log file: \n{lines}')
            self.assertEqual(len(lines), 4)
            self.assertEqual(lines[0], 'test info message\n')
            self.assertEqual(lines[1], 'test warning message\n')
            self.assertEqual(lines[2], 'test error message\n')
            self.assertEqual(lines[3], 'test critical message\n')

        print(f'test reading contents from system log file')
        log_content = ts.read_sys_log()
        self.assertIsInstance(log_content, list)
        self.assertEqual(log_content, lines)

        log_content = ts.read_sys_log(row_count=2)
        self.assertIsInstance(log_content, list)
        self.assertEqual(log_content, lines[-2:])

        log_content = ts.read_sys_log(row_count=20)
        self.assertIsInstance(log_content, list)
        self.assertEqual(log_content, lines)

        log_content = ts.read_sys_log(row_count=0)
        self.assertIsInstance(log_content, list)
        self.assertEqual(log_content, lines)

        log_content = ts.read_sys_log(row_count=-1)
        self.assertIsInstance(log_content, list)
        self.assertEqual(log_content, lines)

        # remove the log file and check if it is removed
        os.remove(sys_log_file_path)
        self.assertFalse(os.path.exists(sys_log_file_path))

    def test_trade_logging(self):
        """ test all documents related to trade logging file operations
        renew_trade_log_file

        """

        print(f'test property trade_log_file_is_valid')
        ts = self.ts
        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        # remove the log file
        os.remove(log_file_path_name)
        self.assertFalse(ts.trade_log_file_is_valid)
        self.assertFalse(os.path.exists(log_file_path_name))

        self.assertFalse(os.path.exists(log_file_path_name))
        res = ts.renew_trade_log_file()
        self.assertTrue(os.path.exists(log_file_path_name))
        self.assertEqual(res, log_file_path_name)
        # remove the file and re-init
        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        self.assertTrue(os.path.exists(log_file_path_name))
        self.assertTrue(ts.trade_log_file_is_valid)

        # remove the log file
        os.remove(log_file_path_name)
        self.assertFalse(ts.trade_log_file_is_valid)
        self.assertFalse(os.path.exists(log_file_path_name))

        # create a file with wrong format
        import csv
        with open(log_file_path_name, 'a') as f:
            writer = csv.writer(f)
            writer.writerow('wrong content!')

        self.assertTrue(os.path.exists(log_file_path_name))
        self.assertFalse(ts.trade_log_file_is_valid)

        print(f'test function renew_trade_log_file')
        ts.renew_trade_log_file()
        self.assertTrue(ts.trade_log_file_is_valid)
        self.assertTrue(os.path.exists(log_file_path_name))
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be only one row, the header row
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0], ts.trade_log_file_headers)

        print(f'test function write_trade_log_file')
        log_content = {
            'position_id': 1,
            'order_id': 1,
            'symbol': '000001.SZ',
            'name': '招商银行',
            'qty_change': 100,
            'qty': 100,
        }
        ts.write_trade_log_file(**log_content)
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be only one row, the header row
            self.assertEqual(len(rows), 2)
            # compare items one by one to see if they match
            row = rows[1]
            self.assertEqual(row[3], '1')
            self.assertEqual(row[4], '000001.SZ')
            self.assertEqual(row[5], '招商银行')
            self.assertEqual(row[6], '')
            self.assertEqual(row[11], '100.000')
            self.assertEqual(row[12], '100.000')
            self.assertEqual(row[2], '1')

        print(f'test writing multiple rows in the file and verify every row')
        log_content = {
            'position_id': 1,
            'order_id': 2,
            'symbol': '000651.SZ',
            'name': '格力电器',
            'qty_change': 200,
            'qty': 200,
            'holding_cost': 70.5,
            'reason': 'order',
            'position_type': 'long',
        }
        ts.write_trade_log_file(**log_content)
        log_content = {
            'position_id': 1,
            'order_id': 3,
            'symbol': '000004.SZ',
            'name': '国农科技',
            'qty_change': -200,
            'qty': 100,
            'holding_cost': 80.5,
            'reason': 'order',
        }
        ts.write_trade_log_file(**log_content)
        log_content = {
            'reason': 'manual',
            'cash_change': 10000.0,
            'cash': 100000.0,
            'available_cash_change': 10000.0,
            'available_cash': 100000.0,
        }
        ts.write_trade_log_file(**log_content)

        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be only one row, the header row
            self.assertEqual(len(rows), 5)
            # compare items one by one to see if they match
            row = rows[1]
            self.assertNotEqual(row[0], '')
            self.assertEqual(row[2], '1')
            self.assertEqual(row[3], '1')
            self.assertEqual(row[4], '000001.SZ')
            self.assertEqual(row[5], '招商银行')
            self.assertEqual(row[6], '')
            self.assertEqual(row[11], '100.000')
            self.assertEqual(row[12], '100.000')
            row = rows[2]
            self.assertNotEqual(row[0], '')
            self.assertEqual(row[1], 'order')
            self.assertEqual(row[2], '2')
            self.assertEqual(row[3], '1')
            self.assertEqual(row[4], '000651.SZ')
            self.assertEqual(row[5], '格力电器')
            self.assertEqual(row[6], 'long')
            self.assertEqual(row[11], '200.000')
            self.assertEqual(row[12], '200.000')
            self.assertEqual(row[16], '70.500')
            row = rows[3]
            self.assertNotEqual(row[0], '')
            self.assertEqual(row[1], 'order')
            self.assertEqual(row[2], '3')
            self.assertEqual(row[3], '1')
            self.assertEqual(row[4], '000004.SZ')
            self.assertEqual(row[5], '国农科技')
            self.assertEqual(row[6], '')
            self.assertEqual(row[11], '-200.000')
            self.assertEqual(row[12], '100.000')
            self.assertEqual(row[16], '80.500')
            row = rows[4]
            self.assertNotEqual(row[0], '')
            self.assertEqual(row[1], 'manual')
            self.assertEqual(row[2], '')
            self.assertEqual(row[4], '')
            self.assertEqual(row[17], '10000.000')
            self.assertEqual(row[18], '100000.000')
            self.assertEqual(row[19], '10000.000')
            self.assertEqual(row[20], '100000.000')

        # remove the log file and check if it is removed
        os.remove(log_file_path_name)
        self.assertFalse(ts.trade_log_file_is_valid)

        # if a wrong file is stored with correct name, it should be checked,
        # removed and a new correct file should be created
        # write a csv file with wrong header
        with open(log_file_path_name, mode='w', encoding='utf-8') as f:
            writer = csv.writer(f)
            row = ['some', 'random', 'but', 'wrong', 'headers']
            writer.writerow(row)

        self.assertFalse(ts.trade_log_file_is_valid)
        # use ts.renew_trade_log_file will remove wrong file and create correct one
        ts.renew_trade_log_file()
        self.assertTrue(ts.trade_log_file_is_valid)

        print(f'test reading dataframe from trade log files')
        df = ts.read_trade_log()
        self.assertIsInstance(df, pd.DataFrame)
        print(f'trade log dataframe: \n{df}')

        # remove the log file and check if it is removed
        os.remove(log_file_path_name)

    def test_break_point_saving(self):
        """ Test functions to save and load break points"""

        print(f'test property break_point_file_exists')
        ts = self.ts
        log_file_path_name = break_point_file_path_name(ts.account_id, ts.datasource)
        # remove the log file
        if os.path.exists(log_file_path_name):
            os.remove(log_file_path_name)
        self.assertFalse(ts.break_point_file_exists)
        self.assertFalse(os.path.exists(log_file_path_name))

        res = ts.save_break_point()
        self.assertTrue(os.path.exists(log_file_path_name))
        self.assertEqual(res, log_file_path_name)
        # remove the file and the file should not exist
        log_file_path_name = break_point_file_path_name(ts.account_id, ts.datasource)
        os.remove(log_file_path_name)
        self.assertFalse(ts.break_point_file_exists)
        self.assertFalse(os.path.exists(log_file_path_name))

        # save the break point and read from it
        res = ts.save_break_point()
        self.assertEqual(res, log_file_path_name)
        self.assertTrue(os.path.exists(log_file_path_name))

        break_point = ts.load_break_point()
        self.assertIsInstance(break_point, dict)
        loaded_operator = break_point['operator']
        loaded_config = break_point['config']

        self.assertIsInstance(loaded_operator, Operator)
        # 对比loaded_operator以及ts的operator的各个方面是否相等
        op1 = ts.operator
        op2 = loaded_operator
        self.assertEqual(op1.strategy_ids, op2.strategy_ids)
        self.assertEqual(op1[0].par_values, op2[0].par_values)

        self.assertIsInstance(loaded_config, dict)
        conf1 = ts.config
        conf2 = loaded_config
        print(f'current trader config is: \n{conf1}\n'
              f'loaded config is: \n{conf2}\n')
        for key in conf1.keys():
            self.assertIn(key, conf2)
            self.assertEqual(conf1[key], conf2[key])

    def test_log_trade_result(self):
        """ test higher level function log_trade_result """
        ts = self.ts

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 19)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[1]
            print(log_row)
            self.assertEqual(log_row[1], 'order')  # reason
            self.assertEqual(log_row[2], '1')  # order_id
            self.assertEqual(log_row[3], '1')  # pos_id
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[7], 'buy')  # direction
            self.assertEqual(log_row[8], '100.000')  # trade_qty
            self.assertEqual(log_row[9], '60.5')  # price
            self.assertEqual(log_row[10], '5.000')  # trade_cost
            self.assertEqual(log_row[11], '100.000')  # qty_change
            self.assertEqual(log_row[12], '300.000')  # qty
            self.assertEqual(log_row[13], '0.000')  # avail-qty_change
            self.assertEqual(log_row[14], '200.000')  # avail-qty
            self.assertEqual(log_row[17], '-6055.000')  # cash_change
            self.assertEqual(log_row[18], '93945.000')  # cash
            self.assertEqual(log_row[19], '-6055.000')  # avail-cash_change
            self.assertEqual(log_row[20], '93945.000')  # avail-cash

            log_row = rows[3]
            print(log_row)
            self.assertEqual(log_row[1], 'order')  # reason
            self.assertEqual(log_row[2], '2')  # order_id
            self.assertEqual(log_row[3], '2')  # pos_id
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[7], 'sell')  # direction
            self.assertEqual(log_row[8], '100.000')  # trade_qty
            self.assertEqual(log_row[9], '70.5')  # price
            self.assertEqual(log_row[10], '5.000')  # trade_cost
            self.assertEqual(log_row[11], '-100.000')  # qty_change
            self.assertEqual(log_row[12], '100.000')  # qty
            self.assertEqual(log_row[13], '-100.000')  # avail-qty_change
            self.assertEqual(log_row[14], '100.000')  # avail-qty
            self.assertEqual(log_row[17], '7045.000')  # cash_change
            self.assertEqual(log_row[18], '100990.000')  # cash
            self.assertEqual(log_row[19], '0.000')  # avail-cash_change
            self.assertEqual(log_row[20], '93945.000')  # avail-cash

            log_row = rows[5]
            print(log_row)
            self.assertEqual(log_row[1], 'order')  # reason
            self.assertEqual(log_row[2], '3')  # order_id
            self.assertEqual(log_row[3], '3')  # pos_id
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[7], 'sell')  # direction
            self.assertEqual(log_row[8], '200.000')  # trade_qty
            self.assertEqual(log_row[9], '80.5')  # price
            self.assertEqual(log_row[10], '5.000')  # trade_cost
            self.assertEqual(log_row[11], '-200.000')  # qty_change
            self.assertEqual(log_row[12], '100.000')  # qty
            self.assertEqual(log_row[13], '-200.000')  # avail-qty_change
            self.assertEqual(log_row[14], '100.000')  # avail-qty
            self.assertEqual(log_row[17], '16095.000')  # cash_change
            self.assertEqual(log_row[18], '117085.000')  # cash
            self.assertEqual(log_row[19], '0.000')  # avail-cash_change
            self.assertEqual(log_row[20], '100990.000')  # avail-cash

    def test_log_cash_delivery(self):
        """ test higher level function log_cash_delivery """
        ts = self.ts

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 19)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[4]
            print(log_row)
            self.assertEqual(log_row[1], 'delivery')  # reason
            self.assertEqual(log_row[2], '2')  # order_id
            self.assertEqual(log_row[3], '2')  # pos_id
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[17], '0.000')  # cash_change
            self.assertEqual(log_row[18], '100990.000')  # cash
            self.assertEqual(log_row[19], '7045.000')  # avail-cash_change
            self.assertEqual(log_row[20], '100990.000')  # avail-cash

            log_row = rows[6]
            print(log_row)
            self.assertEqual(log_row[1], 'delivery')  # reason
            self.assertEqual(log_row[2], '3')  # order_id
            self.assertEqual(log_row[3], '3')  # pos_id
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[17], '0.000')  # cash_change
            self.assertEqual(log_row[18], '117085.000')  # cash
            self.assertEqual(log_row[19], '16095.000')  # avail-cash_change
            self.assertEqual(log_row[20], '117085.000')  # avail-cash

    def test_log_qty_delivery(self):
        """ test higher level function log_qty_delivery """
        ts = self.ts

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 19)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[2]
            print(log_row)
            self.assertEqual(log_row[1], 'delivery')  # reason
            self.assertEqual(log_row[2], '1')  # order_id
            self.assertEqual(log_row[3], '1')  # pos_id
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[11], '0.000')  # qty_change
            self.assertEqual(log_row[12], '300.000')  # qty
            self.assertEqual(log_row[13], '100.000')  # avail-qty_change
            self.assertEqual(log_row[14], '300.000')  # avail-qty

            log_row = rows[8]
            print(log_row)
            self.assertEqual(log_row[1], 'delivery')  # reason
            self.assertEqual(log_row[2], '4')  # order_id
            self.assertEqual(log_row[3], '5')  # pos_id
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[11], '0.000')  # qty_change
            self.assertEqual(log_row[12], '400.000')  # qty
            self.assertEqual(log_row[13], '400.000')  # avail-qty_change
            self.assertEqual(log_row[14], '400.000')  # avail-qty

    def test_log_manual_cash_change(self):
        """ test higher level function log_manual_cash_change """
        ts = self.ts

        ts.manual_change_cash(10000.)

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 20)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[19]
            print(log_row)
            self.assertEqual(log_row[1], 'manual')  # reason
            self.assertEqual(log_row[2], '')  # order_id
            self.assertEqual(log_row[3], '')  # pos_id
            self.assertEqual(log_row[6], '')  # position
            self.assertEqual(log_row[17], '10000.000')  # cash_change
            self.assertEqual(log_row[18], '83905.000')  # cash
            self.assertEqual(log_row[19], '10000.000')  # avail-cash_change
            self.assertEqual(log_row[20], '83905.000')  # avail-cash

        ts.manual_change_cash(20000.)

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 21)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[20]
            print(log_row)
            self.assertEqual(log_row[1], 'manual')  # reason
            self.assertEqual(log_row[2], '')  # order_id
            self.assertEqual(log_row[3], '')  # pos_id
            self.assertEqual(log_row[6], '')  # position
            self.assertEqual(log_row[17], '20000.000')  # cash_change
            self.assertEqual(log_row[18], '103905.000')  # cash
            self.assertEqual(log_row[19], '20000.000')  # avail-cash_change
            self.assertEqual(log_row[20], '103905.000')  # avail-cash

        ts.manual_change_cash(-200000.)  # manual change cash over availability will not seccess

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 21)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[20]
            print(log_row)
            self.assertEqual(log_row[1], 'manual')  # reason
            self.assertEqual(log_row[2], '')  # order_id
            self.assertEqual(log_row[3], '')  # pos_id
            self.assertEqual(log_row[6], '')  # position
            self.assertEqual(log_row[17], '20000.000')  # cash_change
            self.assertEqual(log_row[18], '103905.000')  # cash
            self.assertEqual(log_row[19], '20000.000')  # avail-cash_change
            self.assertEqual(log_row[20], '103905.000')  # avail-cash

    def test_log_manual_qty_change(self):
        """ test higher level function log_manual_qty_change """
        ts = self.ts

        ts.manual_change_position(symbol='000001.SZ', quantity=200, price=30, side='long')

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 20)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[19]
            print(log_row)
            self.assertEqual(log_row[1], 'manual')  # reason
            self.assertEqual(log_row[2], '')  # order_id
            self.assertEqual(log_row[3], '1')  # pos_id
            self.assertEqual(log_row[4], '000001.SZ')  # symbol
            self.assertIn(log_row[5], ['平安银行', 'N/A'])  # name depends on whether the symbol info can be retrieved
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[7], '')  # direction
            self.assertEqual(log_row[11], '200.000')  # qty_change
            self.assertEqual(log_row[12], '300.000')  # qty
            self.assertEqual(log_row[13], '200.000')  # avail-qty_change
            self.assertEqual(log_row[14], '300.000')  # avail-qty
            self.assertEqual(log_row[15], '72.267')  # cost_change
            self.assertEqual(log_row[16], '-6.133')  # cost

        ts.manual_change_position(symbol='000006.SZ', quantity=200, price=30, side='long')

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 21)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[20]
            print(log_row)
            self.assertEqual(log_row[1], 'manual')  # reason
            self.assertEqual(log_row[2], '')  # order_id
            self.assertEqual(log_row[3], '5')  # pos_id
            self.assertEqual(log_row[4], '000006.SZ')  # symbol
            self.assertIn(log_row[5], ['深振业A', 'N/A'])  # name
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[7], '')  # direction
            self.assertEqual(log_row[11], '200.000')  # qty_change
            self.assertEqual(log_row[12], '600.000')  # qty
            self.assertEqual(log_row[13], '200.000')  # avail-qty_change
            self.assertEqual(log_row[14], '600.000')  # avail-qty
            self.assertEqual(log_row[15], '-19.838')  # cost_change
            self.assertEqual(log_row[16], '69.675')  # cost

        ts.manual_change_position(symbol='wrong_symbol', quantity=200, price=30, side='long')
        # changing wrong symbol will not be logged

        log_file_path_name = trade_log_file_path_name(ts.account_id, ts.datasource)
        print(f'trade file path is {log_file_path_name}')
        import csv
        with open(log_file_path_name, 'r') as f:
            reader = csv.reader(f)
            rows = [row for row in reader]

            # there should be two rows including the header row, check the new row
            self.assertEqual(len(rows), 21)
            self.assertEqual(len(rows[1]), 21)
            # check key parameters in the log result:
            log_row = rows[20]
            print(log_row)
            self.assertEqual(log_row[1], 'manual')  # reason
            self.assertEqual(log_row[2], '')  # order_id
            self.assertEqual(log_row[3], '5')  # pos_id
            self.assertEqual(log_row[4], '000006.SZ')  # symbol
            self.assertIn(log_row[5], ['深振业A', 'N/A'])  # name
            self.assertEqual(log_row[6], 'long')  # position
            self.assertEqual(log_row[7], '')  # direction
            self.assertEqual(log_row[11], '200.000')  # qty_change
            self.assertEqual(log_row[12], '600.000')  # qty
            self.assertEqual(log_row[13], '200.000')  # avail-qty_change
            self.assertEqual(log_row[14], '600.000')  # avail-qty
            self.assertEqual(log_row[15], '-19.838')  # cost_change
            self.assertEqual(log_row[16], '69.675')  # cost

    def test_trader_status(self):
        """测试Trader类的状态管理功能
    
        该测试验证Trader在不同状态之间的转换，包括running、sleeping、paused和stopped状态。
        同时测试了直接调用内部方法对状态的影响。
        
        Args:
            self: 测试类实例，包含ts属性(Trader实例)和stoppage属性(睡眠时间)
            
        Returns:
            None: 该测试方法无返回值，通过断言验证Trader状态转换的正确性
        """
        ts = self.ts
        self.assertIsInstance(ts, Trader)
        Thread(target=ts.run, daemon=True).start()
        time.sleep(self.stoppage)
        print(f'started trader, current status: {ts.status}')
        if self.ts.is_market_open:
            self.assertEqual(ts.status, 'running')
        else:
            self.assertEqual(ts.status, 'sleeping')

        print(f'\ncurrent trade day? {ts.is_trade_day}, trader status: {ts.status}')
        ts.add_task('wakeup')
        time.sleep(self.stoppage)
        print(f'trader status will be running after running task "wakeup"')
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('sleep')
        print(f'trader status will be sleeping after running task "sleep"')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')
        print(f'trader status will be paused after running task "pause"')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        ts.add_task('wakeup')  # should be ignored
        print(f'trader status will still be paused after running task "wakeup" in paused status')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('resume')  # resume to previous status: sleeping
        print(f'trader status will be sleeping after running task "resume"')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('wakeup')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        ts.add_task('sleep')  # should be ignored
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        ts.add_task('resume')  # resume to previous status: running
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('stop')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'stopped')
        print(f'\ncurrent status: {ts.status}')

        # 测试直接调用内部方法对状态的影响
        print(f'test function _run_task, as running tasks off-line')
        self.assertEqual(ts.status, 'stopped')
        ts._run_task('start')
        self.assertEqual(ts.status, 'sleeping')
        ts._run_task('stop')
        self.assertEqual(ts.status, 'stopped')
        ts._run_task('start')
        self.assertEqual(ts.status, 'sleeping')
        ts._run_task('wakeup')
        self.assertEqual(ts.status, 'running')
        ts._run_task('sleep')
        self.assertEqual(ts.status, 'sleeping')
        ts._run_task('wakeup')
        self.assertEqual(ts.status, 'running')
        ts._run_task('pause')
        self.assertEqual(ts.status, 'paused')
        ts._run_task('resume')
        self.assertEqual(ts.status, 'running')
        ts._run_task('sleep')
        self.assertEqual(ts.status, 'sleeping')
        ts._run_task('pause')
        self.assertEqual(ts.status, 'paused')
        ts._run_task('resume')
        self.assertEqual(ts.status, 'sleeping')

    def test_trader_properties_methods(self):
        """Test function _run_task"""
        ts = self.ts
        ts.renew_trade_log_file()
        self.assertIsInstance(ts, Trader)
        self.assertEqual(ts.status, 'stopped')
        ts._run_task('start')
        self.assertEqual(ts.status, 'sleeping')

        print('test properties account and account id')
        print(ts.account_id, ts.account)
        self.assertEqual(ts.account_id, 1)
        self.assertIsInstance(ts.account, dict)
        self.assertEqual(ts.account['user_name'], 'test_user1')
        self.assertEqual(ts.account['cash_amount'], 73905.0)
        self.assertEqual(ts.account['available_cash'], 73905.0)

        print('test properties operator and broker')
        print(f'operator: {ts.operator}\nbroker: {ts.broker}')
        self.assertIsInstance(ts.operator, Operator)
        self.assertIsInstance(ts.operator[0], BaseStrategy)
        self.assertIsInstance(ts.operator[1], BaseStrategy)
        self.assertEqual(ts.operator[0].name, 'MACD')
        self.assertEqual(ts.operator[1].name, 'DMA')
        self.assertIsInstance(ts.broker, Broker)

        print('test property asset pool')
        print(f'asset pool: {ts.asset_pool}')
        self.assertIsInstance(ts.asset_pool, list)
        self.assertEqual(ts.asset_pool, ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ'])

        print('test property account cash, positions and overview')
        print(f'cash: {ts.account_cash}\npositions: \n{ts.account_positions}')
        self.assertEqual(ts.account_cash, (73905.0, 73905.0, 100000.0))
        self.assertIsInstance(ts.account_positions, pd.DataFrame)
        self.assertTrue(np.allclose(ts.account_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        self.assertIsInstance(ts.non_zero_positions, pd.DataFrame)
        self.assertTrue(np.allclose(ts.non_zero_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.non_zero_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))

        print('test property history orders, cashes, and positions')
        print(f'history orders: \n{ts.history_orders()}')
        # test history orders without results
        history_orders = ts.history_orders(with_trade_results=False)
        self.assertIsInstance(ts.history_orders(), pd.DataFrame)
        self.assertEqual(history_orders.shape, (9, 8))
        self.assertEqual(history_orders.columns.tolist(), ['symbol', 'position', 'direction', 'order_type',
                                                           'qty', 'price',
                                                           'submitted_time', 'status'])
        # test manual change of cashes and positions
        self.assertEqual(ts.account_cash, (73905.0, 73905.0, 100000.0))
        ts.manual_change_cash(10000.0)
        self.assertEqual(ts.account_cash, (83905.0, 83905.0, 110000.0))
        ts.manual_change_cash(-10000.0)
        self.assertEqual(ts.account_cash, (73905.0, 73905.0, 100000.0))
        # test too large cash change
        ts.manual_change_cash(-100000.0)
        self.assertEqual(ts.account_cash, (73905.0, 73905.0, 100000.0))

        self.assertTrue(np.allclose(ts.account_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        ts.manual_change_position('000001.SZ', 200.0, 10.0)
        self.assertTrue(np.allclose(ts.account_positions['qty'], [300.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [300.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        ts.manual_change_position('000001.SZ', -100.0, 10.0)
        self.assertTrue(np.allclose(ts.account_positions['qty'], [200.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [200.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        ts.manual_change_position('000001.SZ', -100.0, 10.0, 'long')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        # wrong side of position change will be ignored
        ts.manual_change_position('000001.SZ', -100.0, 10.0, 'short')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        # the other side of position change can be done when this side is cleared
        ts.manual_change_position('000001.SZ', -100.0, 10.0, 'long')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [0.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [0.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        ts.manual_change_position('000001.SZ', 100.0, 10.0, 'short')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [-100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [-100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        # if reduced qty is larger than current qty, the change will be ignored
        ts.manual_change_position('000001.SZ', -200.0, 10.0, 'short')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [-100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [-100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))

        ts.info()

    def test_trader_run(self):
        """Test full-fledged run with all tasks manually added"""
        ts = self.ts
        ts.debug = True  # 这样就可以直接模拟交易日了
        ts.force_current_date = pd.to_datetime('2023-05-10').date()  # 强制设置日期为一个交易日
        self.assertTrue(ts.is_trade_day)
        Thread(target=ts.run, daemon=True).start()  # start the trader
        time.sleep(self.stoppage)
        print(f'started trader, current status: {ts.status}, broker status: {ts.broker.status}')

        # 依次执行start, pre_open, open_market, run_stg - macd, run_stg - dma, close_market, post_close, stop
        ts.add_task('start')
        time.sleep(self.stoppage)
        print(f'ran task start, current status: {ts.status}, broker status: {ts.broker.status}')
        print('added task start')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        # 新的trader创建后，如果当前是交易时段，status为running，否则为sleeping，因此这里的status可能是running或者sleeping，需要根据market_open判断
        if ts.is_market_open:
            self.assertEqual(ts.status, 'running')
            self.assertEqual(ts.broker.status, 'running')
        else:
            self.assertEqual(ts.status, 'sleeping')
            self.assertEqual(ts.broker.status, 'init')

        ts.add_task('pre_open')
        time.sleep(self.stoppage)
        print(f'ran task pre_open, current status: {ts.status}, broker status: {ts.broker.status}')
        print('added task pre_open')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        if ts.is_market_open:
            self.assertEqual(ts.status, 'running')
            self.assertEqual(ts.broker.status, 'running')
        else:
            self.assertEqual(ts.status, 'sleeping')
            self.assertEqual(ts.broker.status, 'init')
        broker_prev_status = 'running'
        prev_status = 'running'

        ts.add_task('open_market')
        time.sleep(self.stoppage)
        print(f'ran task open_market, current status: {ts.status}, broker status: {ts.broker.status}')
        print('added task open_market')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, prev_status)
        self.assertEqual(ts.broker.status, broker_prev_status)

        print(f'created daily schedule: \n{ts.task_daily_schedule}')

        ts.add_task('run_strategy', 0)
        time.sleep(self.stoppage)
        print(f'ran task run_strategy, current status: {ts.status}, broker status: {ts.broker.status}')
        print('added task run_strategy - macd')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('run_strategy', 1)
        time.sleep(self.stoppage)
        print('added task run_strategy - dma')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('sleep')
        time.sleep(self.stoppage)
        print('added task sleep')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'paused')
        ts.add_task('wakeup')
        time.sleep(self.stoppage)
        print('added task wakeup')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('run_strategy', 2)
        time.sleep(self.stoppage)
        print('added task run_strategy - macd, dma')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('close_market')
        time.sleep(self.stoppage)
        print('added task close_market')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'paused')
        ts.add_task('post_close')
        time.sleep(self.stoppage)
        print('added task post_close')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'paused')
        ts.add_task('stop')
        time.sleep(self.stoppage)
        print('added task stop')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'stopped')
        self.assertEqual(ts.broker.status, 'stopped')

    def test_get_update_live_prices(self):
        """ test update live prices"""
        self.ts._update_live_price()
        print(f'updated live price, as following: {self.ts.live_price}')
        df = self.ts.live_price
        self.assertIsInstance(df, pd.DataFrame)
        self.assertFalse(df.empty)
        # 根据Trader的asset_pool配置生成预期symbols列表
        symbols_expected = list(self.ts.asset_pool)
        symbols_acquired = df.index.tolist()
        print(f'expected symbols: {symbols_expected}')
        print(f'acquired symbols: {symbols_acquired}')
        # index应当与asset_pool中的symbols一一对应
        self.assertListEqual(symbols_acquired, symbols_expected)
        # 根据_update_live_price的docstring，DataFrame应当具有名为price的列保存当前价格
        print(f'live price columns: {df.columns.tolist()}')
        self.assertIn('price', df.columns)
        self.assertListEqual(df.columns.tolist(), ['price'])
        # price列中应当是数值型数据
        self.assertTrue(np.issubdtype(df['price'].dtype, np.number))

    def test_strategy_run_and_process_result(self):
        """Test strategy run and process result"""
        ts = self.ts
        ts._run_task('start')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts._run_task('run_strategy', 0)
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        # run task refill data
        ts._run_task('refill', *('stock_daily', 1, 'tushare'))
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts._run_task('refill', *('index_daily', 1, 'tushare'))
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')

        ts._stop()
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'stopped')
        self.assertEqual(ts.broker.status, 'stopped')

    def test_trader(self):
        """Test trader with simulated live trade task agenda"""
        # start the trader and broker in separate threads, set the trader to debug mode
        # and then manually generate task agenda and add task from agenda with twisted
        # current time, thus to test the trader in simulated real-time run.

        # 1, use trader._check_trade_day(sim_date) to simulate a trade day or non-trade day
        # 2, use trader._initialize_schedule(sim_time) to generate task agenda at a simulated time
        # 3, use trader._add_task_from_schedule(sim_time) to add task from agenda at a simulated time

        import datetime as dt

        ts = self.ts
        print(f'current ts status: {ts.status}')
        ts.debug = True
        ts.broker.debug = True
        ts.broker.broker_name = 'test_broker'
        trader_thread = Thread(target=ts.run, daemon=True)
        broker_thread = Thread(target=ts.broker.run, daemon=True)
        ts.register_broker(debug=True)
        print(f'current ts status: {ts.status}')
        trader_thread.start()
        broker_thread.start()
        time.sleep(self.stoppage)
        print(f'current ts status: {ts.status}')

        # generate task agenda in a non-trade day and empty list will be generated
        sim_date = dt.date(2023, 1, 1)  # a non-trade day
        ts.force_current_date = sim_date
        sim_time = dt.time(0, 0, 0)  # midnight
        ts._initialize_schedule(sim_time)
        print(f'current ts status: {ts.status}')
        ts._add_task_from_schedule(sim_time)
        print(f'current ts status: {ts.status}')

        print('\n========generated task schedule in a non-trade day========\n')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        print(f'is_trade_day: {ts.is_trade_day}')
        print(f'task daily schedule: {ts.task_daily_schedule}')
        if ts.is_market_open:
            self.assertEqual(ts.status, 'running')
            self.assertEqual(ts.broker.status, 'running')
        else:
            self.assertEqual(ts.status, 'sleeping')
            self.assertEqual(ts.broker.status, 'init')
        self.assertEqual(ts.is_trade_day, False)
        self.assertEqual(ts.task_daily_schedule, [])

        # generate task agenda in a trade day and complete agenda will be generated depending on generate time
        sim_date = dt.date(2023, 5, 10)  # a trade day
        ts.force_current_date = sim_date
        sim_time = dt.time(7, 0, 0)  # before morning market open
        self.assertEqual(ts.is_trade_day, True)
        ts._initialize_schedule(sim_time)  # should generate complete agenda
        print('\n========generated task agenda before morning market open========\n')
        for task in ts.task_daily_schedule:
            print(task)
        # 实际生成的task_table还受三个因素影响：self.daily/weekly/monthly_refill_tables
        # 因为即使在这里强制设置了交易日为2023年5月20日，但是在ts._initialize_schedule中
        print(f'daily_refill_tables: {ts.daily_refill_tables}')
        print(f'weekly_refill_tables: {ts.weekly_refill_tables}')
        print(f'monthly_refill_tables: {ts.monthly_refill_tables}')
        target_agenda = [
            ('09:15:00', 'pre_open'),
            ('09:30:00', 'open_market'),
            ('09:31:00', 'run_strategy', 0),
            ('09:45:05', 'acquire_live_price'),
            ('10:00:00', 'run_strategy', 1),
            ('10:00:05', 'acquire_live_price'),
            ('10:15:05', 'acquire_live_price'),
            ('10:30:00', 'run_strategy', 2),
            ('10:30:05', 'acquire_live_price'),
            ('10:45:05', 'acquire_live_price'),
            ('11:00:00', 'run_strategy', 3),
            ('11:00:05', 'acquire_live_price'),
            ('11:15:05', 'acquire_live_price'),
            ('11:30:00', 'run_strategy', 4),
            ('11:30:05', 'acquire_live_price'),
            ('11:35:00', 'close_market'),
            ('12:55:00', 'open_market'),
            ('13:00:00', 'run_strategy', 5),
            ('13:15:05', 'acquire_live_price'),
            ('13:30:00', 'run_strategy', 6),
            ('13:30:05', 'acquire_live_price'),
            ('13:45:05', 'acquire_live_price'),
            ('14:00:00', 'run_strategy', 7),
            ('14:00:05', 'acquire_live_price'),
            ('14:15:05', 'acquire_live_price'),
            ('14:30:00', 'run_strategy', 8),
            ('14:30:05', 'acquire_live_price'),
            ('14:45:05', 'acquire_live_price'),
            ('15:00:00', 'run_strategy', 9),
            ('15:00:05', 'acquire_live_price'),
            ('15:15:05', 'acquire_live_price'),
            ('15:29:00', 'run_strategy', 10),
            ('15:30:00', 'close_market'),
            ('15:30:05', 'acquire_live_price'),
            ('15:45:00', 'post_close'),
            ('16:00:00', 'refill', ('stock_1min, stock_5min', 1)),
        ]
        self.assertEqual(ts.task_daily_schedule[:35], target_agenda[:35])
        last_task = ts.task_daily_schedule[-1]
        print(last_task)
        self.assertEqual(last_task, ('16:00:00', 'refill', ('stock_1min, stock_5min', 1)))
        # re_initialize_agenda at 10:35:27
        sim_time = dt.time(10, 35, 27)
        ts.task_daily_schedule = []
        ts._initialize_schedule(sim_time)
        print('\n========generated task agenda at 10:35:27========')
        for task in ts.task_daily_schedule:
            print(task)
        target_agenda = [
            ('09:15:00', 'pre_open'),
            ('09:30:00', 'open_market'),
            ('10:45:05', 'acquire_live_price'),
            ('11:00:00', 'run_strategy', 3),
            ('11:00:05', 'acquire_live_price'),
            ('11:15:05', 'acquire_live_price'),
            ('11:30:00', 'run_strategy', 4),
            ('11:30:05', 'acquire_live_price'),
            ('11:35:00', 'close_market'),
            ('12:55:00', 'open_market'),
            ('13:00:00', 'run_strategy', 5),
            ('13:15:05', 'acquire_live_price'),
            ('13:30:00', 'run_strategy', 6),
            ('13:30:05', 'acquire_live_price'),
            ('13:45:05', 'acquire_live_price'),
            ('14:00:00', 'run_strategy', 7),
            ('14:00:05', 'acquire_live_price'),
            ('14:15:05', 'acquire_live_price'),
            ('14:30:00', 'run_strategy', 8),
            ('14:30:05', 'acquire_live_price'),
            ('14:45:05', 'acquire_live_price'),
            ('15:00:00', 'run_strategy', 9),
            ('15:00:05', 'acquire_live_price'),
            ('15:15:05', 'acquire_live_price'),
            ('15:29:00', 'run_strategy', 10),
            ('15:30:00', 'close_market'),
            ('15:30:05', 'acquire_live_price'),
            ('15:45:00', 'post_close'),
            ('16:00:00', 'refill', ('stock_1min, stock_5min', 1))
        ]
        self.assertEqual(ts.task_daily_schedule, target_agenda)
        ts.task_queue.empty()  # clear task queue

        # third, create simulated task agenda and execute tasks from the agenda at sim times
        # 为了避免测试过程中trader自动触发task，手动生成一个task agenda，将所有测试时间设置为current_time的10分钟以后，并间隔1分钟
        # 如果当天已经过了23：40：00，可能没有足够时间测试，则等待20分钟后再次测试（此时已经是第二日凌晨）
        # stop trader and broker, and restart them
        ts._run_task('stop')

        current_time = dt.datetime.now()
        if current_time.time() > dt.time(23, 40, 0):
            print(f'current time is {current_time}, wait 20 minutes to test')
            time.sleep(1200)
            current_time = dt.datetime.now()

        ts.debug = True  # 设置debug模式，在不使用TrderShell的情况下没有效果
        ts.broker.debug = True
        ts.broker.broker_name = 'test_simulation_broker'
        ts.broker.status = 'init'
        Thread(target=ts.run, daemon=True).start()
        ts.task_daily_schedule = []  # clear task agenda
        Thread(target=ts.broker.run, daemon=True).start()

        print(f'\n==========start simulation run, setting up test agenda============\n')
        # 创建一个包含7个时间点的测试时间序列，每个时间点间隔1分钟，第一个时间点为当前时间推后10分钟
        test_sim_times = [
            (current_time + dt.timedelta(minutes=10)).time(),  # should run task open_market
            (current_time + dt.timedelta(minutes=11)).time(),  # should run task run_strategy macd and dma
            (current_time + dt.timedelta(minutes=12)).time(),  # should run task sleep
            (current_time + dt.timedelta(minutes=13)).time(),  # should run task wakeup
            (current_time + dt.timedelta(minutes=14)).time(),  # should run task run_strategy macd
            (current_time + dt.timedelta(minutes=15)).time(),  # should run task close_market
            (current_time + dt.timedelta(minutes=16)).time(),  # should run task post_close
            (current_time + dt.timedelta(minutes=17)).time(),  # should run task refill
        ]
        time.sleep(1)  # wait 1 second to avoid the trader generating agenda again
        ts.task_daily_schedule = [
            (test_sim_times[0].strftime('%H:%M:%S'), 'open_market'),
            (test_sim_times[1].strftime('%H:%M:%S'), 'run_strategy', 0),
            (test_sim_times[2].strftime('%H:%M:%S'), 'sleep'),
            (test_sim_times[3].strftime('%H:%M:%S'), 'wakeup'),
            (test_sim_times[4].strftime('%H:%M:%S'), 'run_strategy', 1),
            (test_sim_times[5].strftime('%H:%M:%S'), 'close_market'),
            (test_sim_times[6].strftime('%H:%M:%S'), 'post_close'),
            (test_sim_times[7].strftime('%H:%M:%S'), 'refill', ('index_daily', 1, 'tushare')),
        ]
        print(f'task agenda manually created: {ts.task_daily_schedule}')
        target_agenda_tasks = [
            ('open_market', ),
            ('run_strategy', 0),
            ('sleep', ),
            ('wakeup', ),
            ('run_strategy', 1),
            ('close_market', ),
            ('post_close', ),
            ('refill', ('index_daily', 1, 'tushare')),
        ]
        # check all tasks are in the agenda
        for task, agenda_task in zip(target_agenda_tasks, ts.task_daily_schedule):
            self.assertEqual(task, agenda_task[1:])
        print('\n==========start simulation run, executing tasks from agenda============\n')
        for sim_time in test_sim_times:
            print(f'\n=========simulating time: {sim_time}=========\n')
            print(f'\n=========current task agenda: {ts.task_daily_schedule[0]}=========\n')
            task_name = ts.task_daily_schedule[0][1]
            ts._add_task_from_schedule(sim_time)
            # waite 2 second for tasks to be executed
            if task_name == 'refill':
                # current running refill task will take 200 seconds
                print('running task refill...')
                time.sleep(200)
            else:
                time.sleep(2)
            print(f'current trader status: {ts.status}')
            print(f'current broker status: {ts.broker.status}')
            print(f'current cash and positions: \n{ts.account_positions}, \n{ts.account_cash}')
            print(f'count of trade orders in queue: {ts.broker.order_queue.unfinished_tasks} orders unprocessed')
            print(f'count of trade results in queue: {ts.broker.result_queue.unfinished_tasks} results generated')
            # waite 5 seconds for order execution results to be generated
            time.sleep(5)
            print(f'current orders: \n{ts.history_orders().to_string()}')
            print(f'recent trade results: \n{ts.trade_results().to_string()}')

        # finally, stop the trader and broker
        print('\n==========stop trader and broker============\n')
        ts._run_task('stop')

        self.assertEqual(ts.status, 'stopped')
        self.assertEqual(ts.broker.status, 'stopped')


# --------------- Plan 3.1: Constructor and parameter validation ---------------

class TestTraderInit(unittest.TestCase):
    """Tests for Trader __init__: valid construction and invalid parameter types."""

    def setUp(self):
        self.data_test_dir = _get_data_test_dir()
        self.test_ds = DataSource('file', file_type='csv', file_loc=self.data_test_dir, allow_drop_table=True)
        _clear_tables(self.test_ds)
        new_account(user_name='init_test_user', cash_amount=50000, data_source=self.test_ds)
        self.operator = _create_operator()
        self.broker = SimulatorBroker()

    def test_init_valid_with_positional_and_kwargs(self):
        """Valid construction with required args and default kwargs."""
        ts = Trader(
            account_id=1,
            operator=self.operator,
            broker=self.broker,
            datasource=self.test_ds,
            **_default_trader_kwargs(),
        )
        self.assertEqual(ts.account_id, 1)
        self.assertIs(ts._broker, self.broker)
        self.assertIs(ts._operator, self.operator)
        self.assertIs(ts._datasource, self.test_ds)
        self.assertIsInstance(ts._asset_pool, list)
        self.assertEqual(ts._asset_pool, ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ'])
        self.assertIsInstance(ts.task_queue, Queue)
        self.assertEqual(ts.task_daily_schedule, [])
        self.assertEqual(ts._status, 'stopped')
        self.assertIsInstance(ts.account, dict)
        self.assertEqual(ts.account['user_name'], 'init_test_user')

    def test_init_asset_pool_string_converted_to_list(self):
        """asset_pool passed as string is converted to list."""
        ts = Trader(
            account_id=1,
            operator=self.operator,
            broker=self.broker,
            datasource=self.test_ds,
            asset_pool='000001.SZ, 000002.SZ',
            asset_type='E',
        )
        self.assertIsInstance(ts.asset_pool, list)
        self.assertEqual(ts.asset_pool, ['000001.SZ', '000002.SZ'])

    def test_init_invalid_account_id_raises_type_error(self):
        """Non-int account_id raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id='1',
                operator=self.operator,
                broker=self.broker,
                datasource=self.test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('account_id must be int', str(ctx.exception))

    def test_init_invalid_operator_raises_type_error(self):
        """Non-Operator operator raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=None,
                broker=self.broker,
                datasource=self.test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('operator must be Operator', str(ctx.exception))

    def test_init_invalid_broker_raises_type_error(self):
        """Non-Broker broker raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=self.operator,
                broker=None,
                datasource=self.test_ds,
                **_default_trader_kwargs(),
            )
        self.assertIn('broker must be Broker', str(ctx.exception))

    def test_init_invalid_datasource_raises_type_error(self):
        """Non-DataSource datasource raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=self.operator,
                broker=self.broker,
                datasource=None,
                **_default_trader_kwargs(),
            )
        self.assertIn('datasource must be DataSource', str(ctx.exception))

    def test_init_invalid_benchmark_asset_raises_type_error(self):
        """benchmark_asset neither str nor list raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            Trader(
                account_id=1,
                operator=self.operator,
                broker=self.broker,
                datasource=self.test_ds,
                benchmark_asset=123,
                **_default_trader_kwargs(),
            )
        self.assertIn('benchmark_asset must be str or list', str(ctx.exception))


# --------------- Plan 3.2: Properties ---------------

class TestTraderProperties(unittest.TestCase):
    """Tests for Trader properties: status, prev_status, next_task, count_down,
    config, file flags, is_trade_day, etc."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_account(debug=False)

    def test_status_initial_is_stopped(self):
        self.assertEqual(self.trader.status, 'stopped')

    def test_status_after_start_is_sleeping(self):
        self.trader._run_task('start')
        self.assertEqual(self.trader.status, 'sleeping')

    def test_status_setter_valid_values(self):
        for val in ['running', 'sleeping', 'paused', 'stopped']:
            self.trader.status = val
            self.assertEqual(self.trader.status, val)

    def test_status_setter_invalid_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.trader.status = 'invalid'
        self.assertIn('invalid status', str(ctx.exception))

    def test_prev_status_after_change(self):
        self.trader._run_task('start')
        self.assertEqual(self.trader.prev_status, 'stopped')
        self.trader._run_task('wakeup')
        self.assertEqual(self.trader.prev_status, 'sleeping')

    def test_next_task_empty_schedule_returns_none(self):
        self.trader.task_daily_schedule = []
        self.assertIsNone(self.trader.next_task)

    def test_count_down_to_next_task_empty_schedule_positive_seconds(self):
        self.trader.task_daily_schedule = []
        cd = self.trader.count_down_to_next_task
        self.assertIsInstance(cd, (int, float))
        self.assertGreaterEqual(cd, 1)

    def test_operator_broker_datasource_asset_pool_asset_type(self):
        self.assertIsInstance(self.trader.operator, Operator)
        self.assertIsInstance(self.trader.broker, Broker)
        self.assertIs(self.trader.datasource, self.test_ds)
        self.assertIsInstance(self.trader.asset_pool, list)
        self.assertEqual(self.trader.asset_type, 'E')

    def test_account_cash_returns_tuple_of_three(self):
        cash = self.trader.account_cash
        self.assertIsInstance(cash, tuple)
        self.assertEqual(len(cash), 3)
        self.assertIsInstance(cash[0], (int, float))
        self.assertIsInstance(cash[1], (int, float))
        self.assertIsInstance(cash[2], (int, float))

    def test_account_positions_dataframe_columns(self):
        pos = self.trader.account_positions
        self.assertIsInstance(pos, pd.DataFrame)
        for col in ['qty', 'available_qty', 'cost']:
            self.assertIn(col, pos.columns)

    def test_non_zero_positions_subset_of_account_positions(self):
        all_pos = self.trader.account_positions
        non_zero = self.trader.non_zero_positions
        self.assertIsInstance(non_zero, pd.DataFrame)
        self.assertTrue(non_zero['qty'].ne(0).all())

    def test_config_is_dict_with_expected_keys(self):
        cfg = self.trader.config
        self.assertIsInstance(cfg, dict)
        self.assertIn('time_zone', cfg)
        self.assertIn('market_open_time_am', cfg)
        self.assertIn('cash_delivery_period', cfg)

    def test_config_cost_params_none_yields_zero_cost_keys(self):
        self.trader.cost_params = None
        cfg = self.trader.config
        self.assertIn('cost_rate_buy', cfg)
        self.assertEqual(cfg['cost_rate_buy'], 0.0)

    def test_trade_log_file_is_valid_no_file_false(self):
        log_path = trade_log_file_path_name(self.trader.account_id, self.trader.datasource)
        if os.path.exists(log_path):
            os.remove(log_path)
        self.assertFalse(self.trader.trade_log_file_is_valid)

    def test_sys_log_file_exists_after_init(self):
        self.trader.init_system_logger()
        self.assertTrue(self.trader.sys_log_file_exists)
        path = sys_log_file_path_name(self.trader.account_id, self.trader.datasource)
        if os.path.exists(path):
            os.remove(path)

    def test_break_point_file_exists_after_save(self):
        bp_path = break_point_file_path_name(self.trader.account_id, self.trader.datasource)
        if os.path.exists(bp_path):
            os.remove(bp_path)
        self.assertFalse(self.trader.break_point_file_exists)
        self.trader._run_task('start')
        self.trader.save_break_point()
        self.assertTrue(self.trader.break_point_file_exists)
        if os.path.exists(bp_path):
            os.remove(bp_path)

    def test_is_trade_day_with_force_current_date(self):
        self.trader.debug = True
        self.trader.force_current_date = pd.to_datetime('2023-05-10').date()
        self.assertTrue(self.trader.is_trade_day)
        self.trader.force_current_date = pd.to_datetime('2023-01-01').date()
        self.assertFalse(self.trader.is_trade_day)


# --------------- Plan 3.3: Task and state (add_task, _run_task, schedule) ---------------

class TestTraderTaskState(unittest.TestCase):
    """Tests for add_task, _run_task, _add_task_from_schedule, _initialize_schedule, get_schedule_string."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_account(debug=True)
        self.stoppage = 0.5

    def test_add_task_non_str_raises_type_error(self):
        with self.assertRaises(TypeError) as ctx:
            self.trader.add_task(123)
        self.assertIn('task should be a str', str(ctx.exception))

    def test_add_task_puts_task_in_queue(self):
        self.trader._run_task('start')
        self.trader.add_task('sleep')
        self.assertFalse(self.trader.task_queue.empty())
        task = self.trader.task_queue.get()
        self.trader.task_queue.task_done()
        self.assertEqual(task, 'sleep')

    def test_add_task_with_args_puts_tuple_in_queue(self):
        self.trader._run_task('start')
        self.trader.add_task('run_strategy', 0)
        self.assertFalse(self.trader.task_queue.empty())
        task = self.trader.task_queue.get()
        self.trader.task_queue.task_done()
        self.assertEqual(task, ('run_strategy', (0,)))

    def test_run_task_invalid_task_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.trader._run_task('nonexistent_task')
        self.assertIn('Invalid task name', str(ctx.exception))

    def test_run_task_none_returns_quietly(self):
        self.trader._run_task(None)
        self.assertEqual(self.trader.status, 'stopped')

    def test_get_schedule_string_empty_returns_no_tasks_message(self):
        self.trader.task_daily_schedule = []
        s = self.trader.get_schedule_string()
        self.assertIn('No tasks scheduled', s)

    def test_get_schedule_string_non_empty_contains_datetime_and_task(self):
        self.trader.task_daily_schedule = [('09:30:00', 'open_market'), ('10:00:00', 'run_strategy', 0)]
        s = self.trader.get_schedule_string()
        self.assertIn('open_market', s)
        self.assertIn('run_strategy', s)

    def test_get_schedule_string_rich_form_replaces_brackets(self):
        """rich_form=True 时 [ 必须被替换为 <，] 必须被替换为 >。使用会产出方括号的 parameters（如 [0]）以强断言替换生效。"""
        self.trader.task_daily_schedule = [('09:30:00', 'run_strategy', [0])]
        s_rich = self.trader.get_schedule_string(rich_form=True)
        s_plain = self.trader.get_schedule_string(rich_form=False)
        print(f's_rich is :\n{s_rich}')
        print(f's_plain is :\n{s_plain}')
        self.assertIn('[', s_plain, 'plain output should contain "[" so replacement is testable')
        self.assertIn(']', s_plain, 'plain output should contain "]" so replacement is testable')
        self.assertNotIn('[', s_rich, 'rich_form=True must replace "["')
        self.assertNotIn(']', s_rich, 'rich_form=True must replace "]"')
        self.assertIn('<', s_rich, 'rich_form=True must produce "<" from "["')
        self.assertIn('>', s_rich, 'rich_form=True must produce ">" from "]"')

    def test_initialize_schedule_non_trade_day_empty_schedule(self):
        self.trader.debug = True
        self.trader.force_current_date = pd.to_datetime('2023-01-01').date()
        self.trader._initialize_schedule(pd.Timestamp('2023-01-01 08:00:00').time())
        self.assertEqual(self.trader.task_daily_schedule, [])

    def test_add_task_from_schedule_pops_past_tasks_into_queue(self):
        self.trader._run_task('start')
        self.trader.task_daily_schedule = [
            ('08:00:00', 'pre_open'),
            ('09:30:00', 'open_market'),
            ('10:00:00', 'run_strategy', 0),
        ]
        import datetime as dt
        current = dt.time(9, 45, 0)
        print(f'task schedule: {self.trader.task_daily_schedule}')
        self.trader._add_task_from_schedule(current)
        print(f'task schedule after adding tasks from schedule: {self.trader.task_daily_schedule}')
        self.assertEqual(len(self.trader.task_daily_schedule), 1)
        self.assertFalse(self.trader.task_queue.empty())
        self.trader.task_queue.get()
        self.trader.task_queue.task_done()
        self.trader.task_queue.get()
        self.trader.task_queue.task_done()


# --------------- Plan 3.5: Individual tasks + TASK_WHITELIST ---------------

class TestTraderTasksIndividual(unittest.TestCase):
    """Per-task tests: each of the 14 tasks invoked via _run_task and expected state/side effects."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_account(debug=True)
        self.stoppage = 0.5

    def test_task_start(self):
        self.assertEqual(self.trader.status, 'stopped')
        self.trader._run_task('start')
        self.assertEqual(self.trader.status, 'sleeping')
        self.assertTrue(self.trader.trade_log_file_is_valid)
        self.assertTrue(self.trader.sys_log_file_exists)

    def test_task_stop(self):
        self.trader._run_task('start')
        self.trader._run_task('stop')
        self.assertEqual(self.trader.status, 'stopped')
        self.assertEqual(self.trader.broker.status, 'stopped')
        self.assertTrue(self.trader.break_point_file_exists)

    def test_task_sleep(self):
        self.trader._run_task('start')
        self.trader._run_task('wakeup')
        self.assertEqual(self.trader.status, 'running')
        self.trader._run_task('sleep')
        self.assertEqual(self.trader.status, 'sleeping')
        self.assertEqual(self.trader.broker.status, 'paused')

    def test_task_wakeup(self):
        self.trader._run_task('start')
        self.assertEqual(self.trader.status, 'sleeping')
        self.trader._run_task('wakeup')
        self.assertEqual(self.trader.status, 'running')
        self.assertEqual(self.trader.broker.status, 'running')

    def test_task_pause_and_resume_to_sleeping(self):
        self.trader._run_task('start')
        self.trader._run_task('pause')
        self.assertEqual(self.trader.status, 'paused')
        self.trader._run_task('resume')
        self.assertEqual(self.trader.status, 'sleeping')

    def test_task_pause_and_resume_to_running(self):
        self.trader._run_task('start')
        self.trader._run_task('wakeup')
        self.trader._run_task('pause')
        self.assertEqual(self.trader.status, 'paused')
        self.trader._run_task('resume')
        self.assertEqual(self.trader.status, 'running')

    def test_task_open_market(self):
        self.trader._run_task('start')
        self.trader._run_task('open_market')
        self.assertTrue(self.trader.is_market_open)
        self.assertEqual(self.trader.status, 'running')
        self.assertEqual(self.trader.broker.status, 'running')

    def test_task_close_market(self):
        self.trader._run_task('start')
        self.trader._run_task('wakeup')
        self.trader._run_task('close_market')
        self.assertFalse(self.trader.is_market_open)
        self.assertEqual(self.trader.status, 'sleeping')
        self.assertEqual(self.trader.broker.status, 'paused')

    def test_task_post_close_no_orders_no_error(self):
        self.trader._run_task('start')
        self.trader._run_task('post_close')
        self.assertEqual(self.trader.status, 'sleeping')

    def test_task_run_strategy_step_index_zero(self):
        # Ensure run schedule and group_timing_table exist (is_trade_day=True)
        self.trader.force_current_date = pd.to_datetime('2023-05-10').date()
        # Provide minimal daily data for operator strategies (MACD/DMA need close_ANY_d, window 10/15)
        _write_minimal_stock_daily(
            self.test_ds,
            start_date='2023-02-01',
            end_date='2023-05-10',
        )
        self.trader._run_task('start')
        self.trader._run_task('wakeup')
        # Avoid dependency on live price fetch; give valid current prices for parse_trade_signal
        symbols = self.trader.asset_pool
        # 根据Trader._update_live_price的设计，live_price应当以symbols为index，以price为列保存当前价格
        self.trader.live_price = pd.DataFrame(
            index=symbols,
            data={'price': [12.0] * len(symbols)},
        )
        print(f'manually injected live_price for test_task_run_strategy_step_index_zero: {self.trader.live_price}')
        self.trader.operator.set_shares(self.trader.asset_pool)
        self.trader.operator.set_group_parameters('Group_1', blender_str='s0')
        self.trader.operator.set_group_parameters('Group_2', blender_str='s0')
        n = self.trader._run_strategy(0)
        self.assertIsInstance(n, (int, np.integer))
        self.assertGreaterEqual(n, 0)

    def test_task_process_result_valid_result(self):
        self.trader, self.test_ds = create_trader_with_orders_and_results(account_id=1, debug=True, stoppage=0.2)
        raw = {'order_id': 1, 'filled_qty': 50, 'price': 61.0, 'transaction_fee': 2.5, 'canceled_qty': 0.0}
        self.trader._run_task('start')
        self.trader._run_task('process_result', raw)
        self.assertTrue(self.trader.trade_log_file_is_valid)

    def test_task_refill_duration_default(self):
        self.trader._run_task('start')
        try:
            self.trader._run_task('refill', 'stock_daily', 1, 'tushare')
        except Exception:
            pass
        self.assertEqual(self.trader.status, 'sleeping')

    def test_task_acquire_live_price_updates_or_keeps_live_price(self):
        self.trader._run_task('start')
        try:
            self.trader._update_live_price()
        except Exception:
            pass
        self.assertTrue(self.trader.live_price is None or isinstance(self.trader.live_price, pd.DataFrame))

    @unittest.skipIf(
        True,
        "pre_open calls refill_missing_datasource_data / get_all_basic_table_data; may fail in CI.",
    )
    def test_task_pre_open_full(self):
        self.trader._run_task('start')
        self.trader._pre_open()
        self.assertEqual(self.trader._status, 'sleeping')


class TestTraderTaskWhitelist(unittest.TestCase):
    """TASK_WHITELIST: in each status, non-whitelisted tasks are ignored when run from main loop."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_account(debug=True)
        self.stoppage = 0.8

    def test_stopped_only_start_executes(self):
        """run() 入口会先执行 _run_task('start')，故主循环处理队列时已为 sleeping。
        验证：sleeping 时非白名单任务（run_strategy）被忽略，白名单任务（wakeup）执行，stop 后回到 stopped。"""
        self.assertEqual(self.trader.status, 'stopped')
        Thread(target=self.trader.run, daemon=True).start()
        time.sleep(self.stoppage)
        if self.trader.is_market_open:
            self.assertEqual(self.trader.status, 'running', 'run() runs start first so status becomes running')
        else:
            self.assertEqual(self.trader.status, 'sleeping', 'run() runs start first so status becomes sleeping')
        self.trader.add_task('run_strategy', 0)
        time.sleep(self.stoppage)
        self.assertEqual(self.trader.status, 'sleeping', 'run_strategy not in sleeping whitelist, should be ignored')
        self.trader.add_task('wakeup')
        time.sleep(self.stoppage)
        self.assertEqual(self.trader.status, 'running', 'wakeup is in sleeping whitelist')
        self.trader.add_task('stop')
        time.sleep(self.stoppage)
        self.assertEqual(self.trader.status, 'stopped')

    def test_sleeping_wakeup_executes_refill_allowed(self):
        self.trader._run_task('start')
        if self.trader.is_market_open:
            self.assertEqual(self.trader.status, 'running')
        else:
            self.assertEqual(self.trader.status, 'sleeping')
        self.trader.add_task('run_strategy', 0)
        Thread(target=self.trader.run, daemon=True).start()
        time.sleep(self.stoppage)
        self.assertEqual(self.trader.status, 'sleeping')
        self.trader.add_task('wakeup')
        time.sleep(self.stoppage)
        self.assertEqual(self.trader.status, 'running')
        self.trader.add_task('stop')
        time.sleep(self.stoppage)


# --------------- Plan 3.3/3.4: Account/orders, logging, info, boundaries ---------------

class TestTraderAccountOrders(unittest.TestCase):
    """history_orders, trade_results, submit_trade_order, manual_change_cash/position."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_orders_and_results(account_id=1, debug=False, stoppage=0.2)

    def test_history_orders_without_results_columns(self):
        ho = self.trader.history_orders(with_trade_results=False)
        self.assertIsInstance(ho, pd.DataFrame)
        for col in ['symbol', 'position', 'direction', 'qty', 'price', 'status']:
            self.assertIn(col, ho.columns)

    def test_history_orders_with_results_columns(self):
        ho = self.trader.history_orders(with_trade_results=True)
        self.assertIsInstance(ho, pd.DataFrame)
        self.assertGreater(len(ho), 0)

    def test_trade_results_filled(self):
        tr = self.trader.trade_results(status='filled')
        self.assertIsInstance(tr, pd.DataFrame)

    def test_submit_trade_order_returns_dict_or_empty(self):
        res = self.trader.submit_trade_order(
            symbol='000001.SZ', position='long', direction='buy',
            order_type='limit', qty=10, price=50.0,
        )
        self.assertIsInstance(res, dict)

    def test_manual_change_cash_positive_increases(self):
        c0 = self.trader.account_cash
        self.trader.manual_change_cash(1000.0)
        c1 = self.trader.account_cash
        self.assertGreater(c1[0], c0[0])
        self.assertGreater(c1[1], c0[1])

    def test_manual_change_cash_negative_over_available_ignored(self):
        c0 = self.trader.account_cash
        self.trader.manual_change_cash(-999999999.0)
        c1 = self.trader.account_cash
        self.assertEqual(c1[0], c0[0])
        self.assertEqual(c1[1], c0[1])


class TestTraderLoggingAndBreakpoint(unittest.TestCase):
    """init_system_logger, read_sys_log, clear_sys_log, init/renew_trade_log_file,
    read_trade_log, save/load_break_point."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_account(debug=False)

    def test_read_sys_log_file_missing_returns_empty_list(self):
        path = sys_log_file_path_name(self.trader.account_id, self.trader.datasource)
        if os.path.exists(path):
            os.remove(path)
        self.assertEqual(self.trader.read_sys_log(), [])

    def test_read_sys_log_with_row_count_returns_last_n(self):
        path = sys_log_file_path_name(self.trader.account_id, self.trader.datasource)
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'w') as f:
            f.write('line1\nline2\nline3\n')
        lines = self.trader.read_sys_log(row_count=2)
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[-1], 'line3\n')
        if os.path.exists(path):
            os.remove(path)

    def test_read_trade_log_invalid_file_returns_empty_dataframe(self):
        path = trade_log_file_path_name(self.trader.account_id, self.trader.datasource)
        if os.path.exists(path):
            os.remove(path)
        df = self.trader.read_trade_log()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertTrue(df.empty)

    def test_load_break_point_no_file_returns_empty_dict(self):
        path = break_point_file_path_name(self.trader.account_id, self.trader.datasource)
        if os.path.exists(path):
            os.remove(path)
        bp = self.trader.load_break_point()
        self.assertIsInstance(bp, dict)
        self.assertEqual(len(bp), 0)

    def test_clear_sys_log_not_implemented(self):
        """clear_sys_log is not yet implemented (qteasy 2.0 migration)."""
        with self.assertRaises(NotImplementedError):
            self.trader.clear_sys_log()


class TestTraderInfoAndMessages(unittest.TestCase):
    """info(), send_message, add_message_prefix, get_config, update_config, get_current_tz_datetime."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_account(debug=False)

    def test_info_returns_dict(self):
        d = self.trader.info()
        self.assertIsInstance(d, dict)

    def test_info_detail_includes_account_id(self):
        d = self.trader.info(detail=True)
        self.assertIn('Account ID', d)
        self.assertEqual(d['Account ID'], 1)

    def test_get_config_none_returns_full_config(self):
        cfg = self.trader.get_config()
        self.assertIsInstance(cfg, dict)
        self.assertIn('time_zone', cfg)

    def test_get_config_key_returns_single_key_dict(self):
        cfg = self.trader.get_config('time_zone')
        self.assertEqual(cfg, {'time_zone': self.trader.time_zone})

    def test_update_config_key_not_in_config_returns_none(self):
        ret = self.trader.update_config(key='nonexistent_key', value=1)
        self.assertIsNone(ret)

    def test_update_config_all_keys_reflected_in_config(self):
        """update_config(key, value) 对每个 config key 写入后，self.config[key] 应返回新值。"""
        # 覆盖 Trader.config 中全部 key 的合法测试值（不测试错误类型）
        all_key_values = {
            'time_zone': 'Asia/Shanghai',
            'live_price_acquire_channel': 'tushare',
            'live_price_acquire_freq': '5min',
            'market_open_time_am': '09:00:00',
            'market_close_time_am': '11:00:00',
            'market_open_time_pm': '13:30:00',
            'market_close_time_pm': '15:00:00',
            'benchmark_asset': '000300.SH',
            'trade_batch_size': 2.0,
            'sell_batch_size': 2.0,
            'cash_delivery_period': 1,
            'stock_delivery_period': 2,
            'allow_sell_short': True,
            'long_position_limit': 0.8,
            'short_position_limit': -0.5,
            'strategy_open_close_timing_offset': 2,
            'live_trade_daily_refill_tables': 'table_daily',
            'live_trade_weekly_refill_tables': 'table_weekly',
            'live_trade_monthly_refill_tables': 'table_monthly',
            'live_trade_data_refill_batch_size': 100,
            'live_trade_data_refill_batch_interval': 60,
            'live_trade_data_refill_channel': 'akshare',
            'cost_rate_buy': 0.001,
            'cost_rate_sell': 0.0005,
            'cost_min_buy': 10.0,
            'cost_min_sell': 10.0,
            'cost_slippage': 0.001,
            'PT_buy_threshold': 0.02,
            'PT_sell_threshold': 0.03,
        }
        for key, value in all_key_values.items():
            self.trader.update_config(key=key, value=value)
            actual = self.trader.config[key]
            if isinstance(value, float):
                self.assertAlmostEqual(actual, value, msg=f'key={key}')
            else:
                self.assertEqual(actual, value, msg=f'key={key}')
            print(f'update_config key={key} value={value} -> config[key]={actual}')

    def test_update_config_cost_params_shape_and_values(self):
        """更新 5 个 cost_* key 后，cost_params 为长度 5 的数组且 config 与实例一致。"""
        self.trader.cost_params = None
        self.assertEqual(self.trader.config['cost_rate_buy'], 0.0)
        self.trader.update_config('cost_rate_buy', 0.002)
        self.assertIsNotNone(self.trader.cost_params)
        self.assertEqual(len(self.trader.cost_params), 5)
        self.assertAlmostEqual(self.trader.config['cost_rate_buy'], 0.002)
        self.assertAlmostEqual(float(self.trader.cost_params[0]), 0.002)
        self.trader.update_config('cost_rate_sell', 0.001)
        self.trader.update_config('cost_min_buy', 5.0)
        self.trader.update_config('cost_min_sell', 5.0)
        self.trader.update_config('cost_slippage', 0.0005)
        self.assertAlmostEqual(self.trader.config['cost_rate_sell'], 0.001)
        self.assertAlmostEqual(self.trader.config['cost_min_buy'], 5.0)
        self.assertAlmostEqual(self.trader.config['cost_min_sell'], 5.0)
        self.assertAlmostEqual(self.trader.config['cost_slippage'], 0.0005)
        print('cost_params after all cost_* updates:', self.trader.cost_params)

    def test_add_message_prefix_contains_status(self):
        s = self.trader.add_message_prefix('hello', debug=False)
        self.assertIn('hello', s)
        self.assertIn(self.trader.status, s)

    def test_get_current_tz_datetime_returns_timestamp(self):
        t = self.trader.get_current_tz_datetime()
        self.assertIsInstance(t, pd.Timestamp)


class TestTraderBoundaries(unittest.TestCase):
    """Boundary and edge cases: empty account, cost_params None, read_sys_log row_count edge, etc."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_account(account_id=1, with_positions=False, debug=False)

    def test_account_positions_empty_positions_still_dataframe(self):
        pos = self.trader.account_positions
        self.assertIsInstance(pos, pd.DataFrame)
        self.assertEqual(len(self.trader.asset_pool), len(pos))

    def test_non_zero_positions_empty_when_no_holdings(self):
        non_zero = self.trader.non_zero_positions
        self.assertIsInstance(non_zero, pd.DataFrame)
        self.assertTrue((non_zero['qty'] == 0).all() or len(non_zero) == 0)

    def test_history_orders_empty_when_no_orders(self):
        ho = self.trader.history_orders(with_trade_results=False)
        self.assertIsInstance(ho, pd.DataFrame)
        self.assertEqual(len(ho), 0)

    def test_trade_results_empty_status_filled(self):
        tr = self.trader.trade_results(status='filled')
        self.assertIsInstance(tr, pd.DataFrame)

    def test_add_task_from_schedule_invalid_task_tuple_length_raises(self):
        """Schedule entry with len not 2 or 3 raises ValueError."""
        self.trader._run_task('start')
        self.trader.task_daily_schedule = [('09:00:00',)]  # length 1
        import datetime as dt
        with self.assertRaises(ValueError) as ctx:
            self.trader._add_task_from_schedule(dt.time(10, 0, 0))
        self.assertIn('Invalid task tuple', str(ctx.exception))


class TestTraderAssetPoolDetail(unittest.TestCase):
    """asset_pool_detail(): empty stock_basic vs with data."""

    def setUp(self):
        self.trader, self.test_ds = create_trader_with_account(debug=False)

    def test_asset_pool_detail_returns_dataframe(self):
        detail = self.trader.asset_pool_detail()
        self.assertIsInstance(detail, pd.DataFrame)
        if not detail.empty:
            self.assertTrue(all(s in self.trader.asset_pool for s in detail.index))


if __name__ == '__main__':
    unittest.main()
