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
        self.assertEqual(tss.status, None)
        self.assertEqual(tss.watch_list, ['000001.SH'])

    def test_command_status(self):
        """ test status command """
        tss = self.tss

        print('testing status command that runs normally and returns None')
        self.assertIsNone(tss.do_status(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_status('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_status('wrong_argument'))

    def test_command_pause(self):
        """ test pause command"""
        tss = self.tss

        print('testing pause command that runs normally and returns None')
        self.assertIsNone(tss.do_pause(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_pause('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_pause('wrong_argument'))

    def test_command_resume(self):
        """ test resume command"""
        tss = self.tss

        print('testing resume command that runs normally and returns None')
        self.assertIsNone(tss.do_resume(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_resume('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_resume('wrong_argument'))

    def test_command_bye(self):
        """ test bye command"""
        tss = self.tss

        print('testing bye command that runs normally and returns True to exit the shell')
        self.assertTrue(tss.do_bye(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_bye('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_bye('wrong_argument'))

    def test_command_stop(self):
        """ test stop command"""
        tss = self.tss

        print('testing stop command that runs normally and returns True to exit the shell')
        self.assertTrue(tss.do_stop(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_stop('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_stop('wrong_argument'))

    def test_command_exit(self):
        """ test exit command"""
        tss = self.tss

        print('testing exit command that runs normally and returns True to exit the shell')
        self.assertTrue(tss.do_exit(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_exit('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_exit('wrong_argument'))

    def test_command_pool(self):
        """ test pool command"""
        tss = self.tss

        raise NotImplementedError('test pool command')

    def test_command_watch(self):
        """ test watch command"""
        tss = self.tss

        print('testing watch command that runs normally and returns None')
        self.assertIsNone(tss.do_watch(''))

        print('testing add a new stock to watch list')
        self.assertIsNone(tss.do_watch('000002.SZ'))
        self.assertEqual(tss.watch_list, ['000001.SH', '000002.SZ'])
        self.assertIsNone(tss.do_watch('000002.SZ'))
        self.assertEqual(tss.watch_list, ['000001.SH', '000002.SZ'])

        print('testing remove a stock from watch list')
        self.assertIsNone(tss.do_watch('-r 000001.SH'))
        self.assertEqual(tss.watch_list, ['000002.SZ'])
        self.assertIsNone(tss.do_watch('-r 000001.SH'))
        self.assertEqual(tss.watch_list, ['000002.SZ'])

        print('testing remove all stocks from watch list')
        self.assertIsNone(tss.do_watch('-c'))
        self.assertEqual(tss.watch_list, [])

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_watch('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_watch('wrong_argument'))

    def test_command_buy(self):
        """ test buy command"""
        tss = self.tss

        print('testing buy command that runs normally and returns None')
        self.assertIsNone(tss.do_buy('000001.SH 100 10.0'))



if __name__ == '__main__':
    unittest.main()