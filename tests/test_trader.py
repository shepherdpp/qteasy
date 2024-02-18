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

from threading import Thread

import pandas as pd
import numpy as np

from qteasy import DataSource, Operator, BaseStrategy
from qteasy.trade_recording import new_account, get_or_create_position, update_position, save_parsed_trade_orders
from qteasy.trading_util import submit_order, process_trade_result, cancel_order, process_account_delivery
from qteasy.trader import Trader
from qteasy.broker import SimulatorBroker, Broker


class TestTrader(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""
        print('Setting up test Trader...')
        operator = Operator(strategies=['macd', 'dma'], op_type='step')
        operator.set_parameter(
                stg_id='dma',
                window_length=20,
                strategy_run_freq='H'
        )
        operator.set_parameter(
                stg_id='macd',
                window_length=30,
                strategy_run_freq='30min',
        )
        broker = SimulatorBroker()
        config = {
            'mode': 0,
            'time_zone': 'local',
            'market_open_time_am':  '09:30:00',
            'market_close_time_pm': '15:30:00',
            'market_open_time_pm':  '13:00:00',
            'market_close_time_am': '11:30:00',
            'exchange':             'SSE',
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
            'asset_pool':           '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
            'asset_type':           'E',
            'PT_buy_threshold':     0.05,
            'PT_sell_threshold':    0.05,
            'allow_sell_short':     False,
            'invest_start':         '2018-01-01',
            'opti_start':           '2018-01-01',
        }
        # 创建测试数据源
        data_test_dir = 'data_test/'
        # 创建一个专用的测试数据源，以免与已有的文件混淆，不需要测试所有的数据源，因为相关测试在test_datasource中已经完成
        test_ds = DataSource('file', file_type='hdf', file_loc=data_test_dir)
        # test_ds = DataSource(
        #         'db',
        #         host=QT_CONFIG['test_db_host'],
        #         port=QT_CONFIG['test_db_port'],
        #         user=QT_CONFIG['test_db_user'],
        #         password=QT_CONFIG['test_db_password'],
        #         db_name=QT_CONFIG['test_db_name']
        # )
        test_ds.reconnect()
        # 清空测试数据源中的所有相关表格数据
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if test_ds.table_data_exists(table):
                test_ds.drop_table_data(table)
        # 创建一个ID=1的账户
        new_account('test_user1', 100000, test_ds)
        # 添加初始持仓
        get_or_create_position(account_id=1, symbol='000001.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000002.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000004.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000005.SZ', position_type='long', data_source=test_ds)
        update_position(position_id=1, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=2, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=3, data_source=test_ds, qty_change=300, available_qty_change=300)
        update_position(position_id=4, data_source=test_ds, qty_change=200, available_qty_change=100)

        # 下载测试所需的基本数据
        print('Downloading test data...')
        # TODO: 这里如果设置parallel=True，会导致下载数据时死锁，原因不明
        test_ds.refill_local_source(
                tables='stock_daily',
                symbols='000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
                start_date='2023-06-04',
                end_date='2023-07-22',
                freqs='D',
                asset_types='E',
                dtypes='close',
                parallel=False,
        )
        self.stoppage = 1.5
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
        # submit orders
        for order_id in order_ids:
            submit_order(order_id, test_ds)

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
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        2,
            'filled_qty':      100,
            'price':           70.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      200,
            'price':           80.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        4,
            'filled_qty':      400,
            'price':           89.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        5,
            'filled_qty':      500,
            'price':           100.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      100,
            'price':           78.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        6,
            'filled_qty':      200,
            'price':           69.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        7,
            'filled_qty':      200,
            'price':           31.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        9,
            'filled_qty':      300,
            'price':           91.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        # order 8 is canceled
        cancel_order(8, test_ds, delivery_config)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)

        print('creating Trader object...')
        # 生成Trader对象
        self.ts = Trader(
                account_id=1,
                operator=operator,
                broker=broker,
                config=config,
                datasource=test_ds,
                debug=False,
        )

    def test_trader_status(self):
        """Test class Trader"""
        ts = self.ts
        self.assertIsInstance(ts, Trader)
        Thread(target=ts.run).start()
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('wakeup')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('sleep')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        ts.add_task('wakeup')  # should be ignored
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'paused')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('resume')  # resume to previous status: sleeping
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

        print(f'test function run_task, as running tasks off-line')
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('stop')
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('wakeup')
        self.assertEqual(ts.status, 'running')
        ts.run_task('sleep')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('wakeup')
        self.assertEqual(ts.status, 'running')
        ts.run_task('pause')
        self.assertEqual(ts.status, 'paused')
        ts.run_task('resume')
        self.assertEqual(ts.status, 'running')
        ts.run_task('sleep')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('pause')
        self.assertEqual(ts.status, 'paused')
        ts.run_task('resume')
        self.assertEqual(ts.status, 'sleeping')

    def test_trader_properties_methods(self):
        """Test function run_task"""
        ts = self.ts
        self.assertIsInstance(ts, Trader)
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
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
        ts._change_cash(10000.0)
        self.assertEqual(ts.account_cash, (83905.0, 83905.0, 110000.0))
        ts._change_cash(-10000.0)
        self.assertEqual(ts.account_cash, (73905.0, 73905.0, 100000.0))
        # test too large cash change
        ts._change_cash(-100000.0)
        self.assertEqual(ts.account_cash, (73905.0, 73905.0, 100000.0))

        self.assertTrue(np.allclose(ts.account_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        ts._change_position('000001.SZ', 200.0, 10.0)
        self.assertTrue(np.allclose(ts.account_positions['qty'], [300.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [300.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        ts._change_position('000001.SZ', -100.0, 10.0)
        self.assertTrue(np.allclose(ts.account_positions['qty'], [200.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [200.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        ts._change_position('000001.SZ', -100.0, 10.0, 'long')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        # wrong side of position change will be ignored
        ts._change_position('000001.SZ', -100.0, 10.0, 'short')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        # the other side of position change can be done when this side is cleared
        ts._change_position('000001.SZ', -100.0, 10.0, 'long')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [0.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [0.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        ts._change_position('000001.SZ', 100.0, 10.0, 'short')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [-100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [-100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))
        # if reduced qty is larger than current qty, the change will be ignored
        ts._change_position('000001.SZ', -200.0, 10.0, 'short')
        self.assertTrue(np.allclose(ts.account_positions['qty'], [-100.0, 100.0, 200.0, 200.0, 400.0, 200.0]))
        self.assertTrue(np.allclose(ts.account_positions['available_qty'], [-100.0, 100.0, 200.0, 100.0, 400.0, 200.0]))

        ts.info()

    def test_trader_run(self):
        """Test full-fledged run with all tasks manually added"""
        ts = self.ts
        Thread(target=ts.run).start()  # start the trader
        time.sleep(self.stoppage)
        # 依次执行start, pre_open, open_market, run_stg - macd, run_stg - dma, close_market, post_close, stop
        ts.add_task('start')
        time.sleep(self.stoppage)
        print('added task start')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts.add_task('pre_open')
        time.sleep(self.stoppage)
        print('added task pre_open')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts.add_task('open_market')
        time.sleep(self.stoppage)
        print('added task open_market')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('run_strategy', {'strategy_ids': ['macd']})
        time.sleep(self.stoppage)
        print('added task run_strategy - macd')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        self.assertEqual(ts.status, 'running')
        self.assertEqual(ts.broker.status, 'running')
        ts.add_task('run_strategy', {'strategy_ids': ['dma']})
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
        ts.add_task('run_strategy', {'strategy_ids': ['macd', 'dma']})
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

    def test_strategy_run_and_process_result(self):
        """Test strategy run and process result"""
        ts = self.ts
        ts.run_task('start')
        time.sleep(self.stoppage)
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        ts.run_task('run_strategy', ['macd', 'dma'])
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
        # 3, use trader._add_task_from_agenda(sim_time) to add task from agenda at a simulated time

        import datetime as dt

        ts = self.ts
        ts.debug = True
        ts.broker.debug = True
        ts.broker.broker_name = 'test_broker'
        trader_thread = Thread(target=ts.run)
        broker_thread = Thread(target=ts.broker.run)
        trader_thread.start()
        broker_thread.start()

        # generate task agenda in a non-trade day and empty list will be generated
        sim_date = dt.date(2023, 1, 1)  # a non-trade day
        sim_time = dt.time(0, 0, 0)  # midnight
        ts._check_trade_day(sim_date)
        ts._initialize_schedule(sim_time)
        ts._add_task_from_agenda(sim_time)

        print('\n========generated task agenda in a non-trade day========\n')
        print(f'trader status: {ts.status}')
        print(f'broker status: {ts.broker.status}')
        print(f'is_trade_day: {ts.is_trade_day}')
        print(f'task daily agenda: {ts.task_daily_schedule}')
        self.assertEqual(ts.status, 'sleeping')
        self.assertEqual(ts.broker.status, 'init')
        self.assertEqual(ts.is_trade_day, False)
        self.assertEqual(ts.task_daily_schedule, [])

        # generate task agenda in a trade day and complete agenda will be generated depending on generate time
        sim_date = dt.date(2023, 5, 10)  # a trade day
        sim_time = dt.time(7, 0, 0)  # before morning market open
        ts._check_trade_day(sim_date)
        self.assertEqual(ts.is_trade_day, True)
        ts._initialize_schedule(sim_time)  # should generate complete agenda
        print('\n========generated task agenda before morning market open========\n')
        print(ts.task_daily_schedule)
        target_agenda = [
            ('09:15:00', 'pre_open'),
            ('09:30:00', 'open_market'),
            ('09:31:00', 'run_strategy', ['macd']),
            ('09:45:05', 'acquire_live_price'),
            ('10:00:00', 'run_strategy', ['macd', 'dma']),
            ('10:00:05', 'acquire_live_price'),
            ('10:15:05', 'acquire_live_price'),
            ('10:30:00', 'run_strategy', ['macd']),
            ('10:30:05', 'acquire_live_price'),
            ('10:45:05', 'acquire_live_price'),
            ('11:00:00', 'run_strategy', ['macd', 'dma']),
            ('11:00:05', 'acquire_live_price'),
            ('11:15:05', 'acquire_live_price'),
            ('11:30:00', 'run_strategy', ['macd']),
            ('11:30:05', 'acquire_live_price'),
            ('11:35:00', 'close_market'),
            ('12:55:00', 'open_market'),
            ('13:00:00', 'run_strategy', ['macd', 'dma']),
            ('13:15:05', 'acquire_live_price'),
            ('13:30:00', 'run_strategy', ['macd']),
            ('13:30:05', 'acquire_live_price'),
            ('13:45:05', 'acquire_live_price'),
            ('14:00:00', 'run_strategy', ['macd', 'dma']),
            ('14:00:05', 'acquire_live_price'),
            ('14:15:05', 'acquire_live_price'),
            ('14:30:00', 'run_strategy', ['macd']),
            ('14:30:05', 'acquire_live_price'),
            ('14:45:05', 'acquire_live_price'),
            ('15:00:00', 'run_strategy', ['macd', 'dma']),
            ('15:00:05', 'acquire_live_price'),
            ('15:15:05', 'acquire_live_price'),
            ('15:29:00', 'run_strategy', ['macd']),
            ('15:30:00', 'close_market'),
            ('15:30:05', 'acquire_live_price'),
            ('15:45:00', 'post_close'),
        ]
        self.assertEqual(ts.task_daily_schedule, target_agenda)
        # re_initialize_agenda at 10:35:27
        sim_time = dt.time(10, 35, 27)
        ts.task_daily_schedule = []
        ts._initialize_schedule(sim_time)
        print('\n========generated task agenda at 10:35:27========')
        print(ts.task_daily_schedule)
        target_agenda = [
            ('09:15:00', 'pre_open'),
            ('09:30:00', 'open_market'),
            ('10:45:05', 'acquire_live_price'),
            ('11:00:00', 'run_strategy', ['macd', 'dma']),
            ('11:00:05', 'acquire_live_price'),
            ('11:15:05', 'acquire_live_price'),
            ('11:30:00', 'run_strategy', ['macd']),
            ('11:30:05', 'acquire_live_price'),
            ('11:35:00', 'close_market'),
            ('12:55:00', 'open_market'),
            ('13:00:00', 'run_strategy', ['macd', 'dma']),
            ('13:15:05', 'acquire_live_price'),
            ('13:30:00', 'run_strategy', ['macd']),
            ('13:30:05', 'acquire_live_price'),
            ('13:45:05', 'acquire_live_price'),
            ('14:00:00', 'run_strategy', ['macd', 'dma']),
            ('14:00:05', 'acquire_live_price'),
            ('14:15:05', 'acquire_live_price'),
            ('14:30:00', 'run_strategy', ['macd']),
            ('14:30:05', 'acquire_live_price'),
            ('14:45:05', 'acquire_live_price'),
            ('15:00:00', 'run_strategy', ['macd', 'dma']),
            ('15:00:05', 'acquire_live_price'),
            ('15:15:05', 'acquire_live_price'),
            ('15:29:00', 'run_strategy', ['macd']),
            ('15:30:00', 'close_market'),
            ('15:30:05', 'acquire_live_price'),
            ('15:45:00', 'post_close'),
        ]
        self.assertEqual(ts.task_daily_schedule, target_agenda)
        ts.task_queue.empty()  # clear task queue

        # third, create simulated task agenda and execute tasks from the agenda at sim times
        # 为了避免测试过程中trader自动触发task，手动生成一个task agenda，将所有测试时间设置为current_time的10分钟以后，并间隔1分钟
        # 如果当天已经过了23：40：00，可能没有足够时间测试，则等待20分钟后再次测试（此时已经是第二日凌晨）
        # stop trader and broker, and restart them
        ts.run_task('stop')

        current_time = dt.datetime.now()
        if current_time.time() > dt.time(23, 40, 0):
            print(f'current time is {current_time}, wait 20 minutes to test')
            time.sleep(1200)
            current_time = dt.datetime.now()

        ts.debug = True  # 设置debug模式，在不使用TrderShell的情况下没有效果
        ts.broker.debug = True
        ts.broker.broker_name = 'test_simulation_broker'
        ts.broker.status = 'init'
        Thread(target=ts.run).start()
        ts.task_daily_schedule = []  # clear task agenda
        Thread(target=ts.broker.run).start()

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
        ]
        time.sleep(1)  # wait 1 second to avoid the trader generating agenda again
        ts.task_daily_schedule = [
            (test_sim_times[0].strftime('%H:%M:%S'), 'open_market'),
            (test_sim_times[1].strftime('%H:%M:%S'), 'run_strategy', ['macd', 'dma']),
            (test_sim_times[2].strftime('%H:%M:%S'), 'sleep'),
            (test_sim_times[3].strftime('%H:%M:%S'), 'wakeup'),
            (test_sim_times[4].strftime('%H:%M:%S'), 'run_strategy', ['macd']),
            (test_sim_times[5].strftime('%H:%M:%S'), 'close_market'),
            (test_sim_times[6].strftime('%H:%M:%S'), 'post_close'),
        ]
        print(f'task agenda manually created: {ts.task_daily_schedule}')
        target_agenda_tasks = [
            ('open_market', ),
            ('run_strategy', ['macd', 'dma']),
            ('sleep', ),
            ('wakeup', ),
            ('run_strategy', ['macd']),
            ('close_market', ),
            ('post_close', ),
        ]
        # check all tasks are in the agenda
        for task, agenda_task in zip(target_agenda_tasks, ts.task_daily_schedule):
            self.assertEqual(task, agenda_task[1:])
        print('\n==========start simulation run, executing tasks from agenda============\n')
        for sim_time in test_sim_times:
            print(f'\n=========simulating time: {sim_time}=========\n')
            print(f'\n=========current task agenda: {ts.task_daily_schedule[0]}=========\n')
            ts._add_task_from_agenda(sim_time)
            # waite 1 second for orders to be generated
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
        ts.run_task('stop')

        self.assertEqual(ts.status, 'stopped')
        self.assertEqual(ts.broker.status, 'stopped')


if __name__ == '__main__':
    unittest.main()

