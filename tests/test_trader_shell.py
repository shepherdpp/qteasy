# coding=utf-8
# ======================================
# File:     test_trader_shell.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-03-04
# Desc:
#   Unittest for trader shell functions
# ======================================

import unittest
import time

from qteasy import DataSource, Operator
from qteasy.trader import Trader, TraderShell
from qteasy.broker import SimulatorBroker


class TestTraderShell(unittest.TestCase):

    def setUp(self):

        config = {
            'mode':                  0,
            'time_zone':             'local',
            'market_open_time_am':   '09:30:00',
            'market_close_time_pm':  '15:30:00',
            'market_open_time_pm':   '13:00:00',
            'market_close_time_am':  '11:30:00',
            'exchange':              'SSE',
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
            'asset_pool':            '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
            'asset_type':            'E',
            'PT_buy_threshold':      0.05,
            'PT_sell_threshold':     0.05,
            'allow_sell_short':      False,
            'invest_start':          '2018-01-01',
            'opti_start':            '2018-01-01',
        }
        # 创建测试数据源
        data_test_dir = 'data_test/'
        # 创建一个专用的测试数据源，以免与已有的文件混淆，不需要测试所有的数据源，因为相关测试在test_datasource中已经完成
        test_ds = DataSource('file', file_type='csv', file_loc=data_test_dir)

        # 创建一个操作员
        operator = Operator(strategies=['macd', 'dma'], op_type='step')
        # 创建一个经纪商
        broker = SimulatorBroker()

        test_ds.reconnect()
        self.ts = Trader(
                account_id=1,
                operator=operator,
                broker=broker,
                config=config,
                datasource=test_ds,
                debug=False,)
        self.ts.debug = True

        self.tss = TraderShell(self.ts)

    def test_properties(self):

        tss = self.tss

        self.assertEqual(tss.trader, self.ts)
        self.assertEqual(tss.status, 'ready')
        self.assertEqual(tss.watch_list, [])

    def test_command_status(self):

        tss = self.tss
        
        arguments = ''
        tss.do_status(arguments)


if __name__ == '__main__':
    unittest.main()