# coding=utf-8
# ======================================
# File:     test_broker.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-04-09
# Desc:
#   Unittest for broker related functions
# ======================================

import unittest
import sys
import tushare as ts
import numpy as np
import pandas as pd
import qteasy as qt
import numba as nb
import talib as ta

from qteasy.trade_recording import new_account, get_or_create_position, record_trade_order, read_trade_order

from qteasy.broker import get_broker, Broker, SimulatorBroker, SimpleBroker, NotImplementedBroker
from qteasy.broker import _verify_trade_result


class TestBroker(unittest.TestCase):

    # TODO: implement the test cases
    #  add test accounts, positions and orders into test system tables,
    #  and test if the results are generated correctly with these test data

    def setUp(self) -> None:
        """ create test accounts, positions and orders """
        print('test environment info: ')
        print(f' python version: {sys.version}')
        print(f' tushare version: {ts.__version__}')
        print(f' numpy version: {np.__version__}')
        print(f' numba version: {nb.__version__}')
        print(f' qteasy version: {qt.__version__}')
        print(f' pandas version: {pd.__version__}')
        print(f' talib version: {ta.__version__}')

        from qteasy import QT_CONFIG, DataSource

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
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_orders']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)

        # 创建一个测试账户
        user_name = 'test_user'
        cash_amount = 10000.0
        new_account(user_name=user_name, cash_amount=cash_amount, data_source=self.test_ds)

        # 在测试账户中创建两个测试持仓
        get_or_create_position(1, '000001.SH', 'long', data_source=self.test_ds)
        get_or_create_position(1, '000002.SH', 'short', data_source=self.test_ds)

        # 在测试账户中创建四个测试订单，分别为两个测试持仓的买入和卖出订单
        test_signal = {
            'pos_id':         1,
            'direction':      'buy',
            'order_type':     'limit',
            'qty':            100,
            'price':          100,
            'submitted_time': '2023-04-09 09:30:00',
            'status':         'created',
        }
        order_id = record_trade_order(test_signal, data_source=self.test_ds)
        # 立即读取order并检查是否成功
        order = read_trade_order(order_id, data_source=self.test_ds)
        print(f'got order with order id ({order_id}): \n{order}')
        test_signal = {
            'pos_id':         1,
            'direction':      'sell',
            'order_type':     'limit',
            'qty':            100,
            'price':          100,
            'submitted_time': '2023-04-09 09:35:00',
            'status':         'created',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'buy',
            'order_type':     'limit',
            'qty':            100,
            'price':          100,
            'submitted_time': '2023-04-09 09:40:00',
            'status':         'submitted',
        }
        record_trade_order(test_signal, data_source=self.test_ds)
        test_signal = {
            'pos_id':         2,
            'direction':      'sell',
            'order_type':     'limit',
            'qty':            100,
            'price':          100,
            'submitted_time': '2023-04-09 09:45:00',
            'status':         'submitted',
        }
        record_trade_order(test_signal, data_source=self.test_ds)

    def test_create_broker(self):
        """ test the function create_broker """
        bkr = Broker(data_source=self.test_ds)
        self.assertIsInstance(bkr, Broker)
        self.assertIs(bkr.data_source, self.test_ds)

    def test_get_broker(self):
        """ test get_broker function """
        bkr = get_broker('simulator', params={'data_source': self.test_ds})
        self.assertIsInstance(bkr, SimulatorBroker)
        self.assertIs(bkr.data_source, self.test_ds)
        bkr = get_broker('simple', params={'data_source': self.test_ds})
        self.assertIsInstance(bkr, SimpleBroker)
        self.assertIs(bkr.data_source, self.test_ds)
        bkr = get_broker('random', params={'data_source': self.test_ds})
        self.assertIsInstance(bkr, SimulatorBroker)
        self.assertIs(bkr.data_source, self.test_ds)
        bkr = get_broker('unknown', params={'data_source': self.test_ds})
        self.assertIsInstance(bkr, SimulatorBroker)
        self.assertIs(bkr.data_source, self.test_ds)
        # Notimplementederror will be raised
        with self.assertRaises(NotImplementedError):
            bkr = get_broker('manual')

    def test_verify_trade_result(self):
        """ test the function _verify_trade_result """

    def test_parse_order(self):
        """ test the function parse_order """
        bkr = get_broker('simple', params={'data_source': self.test_ds})
        order = read_trade_order(1, data_source=self.test_ds)
        print(order)
        order = bkr._parse_order(order)
        print(order)
        self.assertEqual(len(order), 6)
        self.assertEqual(order[0], 'limit')
        self.assertEqual(order[1], '000001.SH')
        self.assertEqual(order[2], 100.0)
        self.assertEqual(order[3], 100.0)
        self.assertEqual(order[4], 'buy')
        self.assertEqual(order[5], 'long')

    def test_get_result(self):
        """ test the function get_result """
        bkr = get_broker('simple', params={'data_source': self.test_ds})
        order = read_trade_order(1, data_source=self.test_ds)
        order['order_id'] = 1
        bkr._get_result(order)
        result = bkr.result_queue.get()
        self.assertIsInstance(result, dict)
        self.assertEqual(result['order_id'], 1)
        self.assertEqual(result['filled_qty'], 100.0)
        self.assertEqual(result['price'], 100.0)
        self.assertEqual(result['canceled_qty'], 0.0)
        self.assertEqual(result['transaction_fee'], 5.0)


if __name__ == '__main__':
    unittest.main()