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

from qteasy import DataSource, Operator
from qteasy.trader import Trader, TraderShell
from qteasy.trading_util import read_trade_order
from qteasy.trade_recording import new_account
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
        # 清空测试数据源中的所有相关表格数据
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if test_ds.table_data_exists(table):
                test_ds.drop_table_data(table)

        # 创建一个ID=1的账户
        new_account('test_user1', 100000, test_ds)

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
        order = read_trade_order()

    def test_command_sell(self):
        """ test sell command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_positions(self):
        """ test positions command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_overview(self):
        """ test overview command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_config(self):
        """ test config command"""
        tss = self.tss

        print(f'testing running with no arguments and print out configs up to level 2')
        self.assertIsNone(tss.do_config(''))
        print(f'testing running with -l 3 and print out configs up to level 3')
        self.assertIsNone(tss.do_config('-lll'))
        print(f'testing running with one key given and print out the value of the key')
        self.assertIsNone(tss.do_config('mode'))
        self.assertIsNone(tss.do_config('time_zone'))
        print(f'testing running with multiple keys given')
        self.assertIsNone(tss.do_config('mode time_zone'))
        print(f'testing running with multiple keys given with details')
        self.assertIsNone(tss.do_config('mode time_zone -d'))
        print(f'testing running with user defined keys')
        self.assertIsNone(tss.do_config('user_defined_key'))
        self.assertIsNone(tss.do_config('user_defined_key -d'))
        print(f'testing running with values to set to config key')
        self.assertEqual(tss.trader.config['mode'], 0)
        self.assertIsNone(tss.do_config('mode -s 1'))
        self.assertEqual(tss.trader.config['mode'], 1)
        self.assertEqual(tss.trader.config['time_zone'], 'local')
        self.assertIsNone(tss.do_config('mode time_zone -s 0 Asia/Shanghai'))
        self.assertEqual(tss.trader.config['mode'], 0)
        self.assertEqual(tss.trader.config['time_zone'], 'Asia/Shanghai')
        self.assertIsNone(tss.do_config('mode time_zone -s 35 Asia/Shanghai'))
        self.assertEqual(tss.trader.config['mode'], 0)

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_config('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_config('user_defined_key -d positional_arg_in_wrong_place'))
        self.assertFalse(tss.do_config('--wrong_optional_arg'))
        self.assertFalse(tss.do_config('-w'))
        self.assertFalse(tss.do_config('argument -l 2'))
        self.assertFalse(tss.do_config('argument -l -s value_1 too_many_set_values'))
        self.assertFalse(tss.do_config('argument too_many_args -s too_few_set_value'))

    def test_command_history(self):
        """ test history command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_orders(self):
        """ test orders command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_change(self):
        """ test change command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_dashboard(self):
        """ test dashboard command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_strategies(self):
        """ test strategies command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_schedule(self):
        """ test schedule command"""
        tss = self.tss

        raise NotImplementedError

    def test_command_run(self):
        """ test run command"""
        tss = self.tss

        raise NotImplementedError

if __name__ == '__main__':
    unittest.main()