# coding=utf-8
# ======================================
# File:     test_trader_shell.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-03-04
# Desc:
#   Unittest for trader shell properties
# and commands.
# ======================================

import unittest
import time
import pandas as pd

from qteasy import DataSource, Operator
from qteasy.trader import Trader
from qteasy.trader_cli import TraderShell
from qteasy.trading_util import process_account_delivery, process_trade_result, submit_order, update_position
from qteasy.trade_recording import new_account, read_trade_order_detail, save_parsed_trade_orders
from qteasy.trade_recording import get_or_create_position, get_position_by_id, get_account
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
            'trade_batch_size':      100,
            'sell_batch_size':       100,
            'PT_buy_threshold':      0.05,
            'PT_sell_threshold':     0.05,
            'allow_sell_short':      False,
            'invest_start':          '2018-01-01',
            'opti_start':            '2018-01-01',
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

        # 创建一个操作员
        operator = Operator(strategies=['macd', 'dma'], op_type='step')
        # 创建一个经纪商
        broker = SimulatorBroker()

        test_ds.reconnect()

        # 创建测试datasource需要的股票基础数据等数据
        stock_basic = {
            'ts_code': ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ'],
            'symbol': ['000001', '000002', '000004', '000005', '000006', '000007'],
            'name': ['平安银行', '万科A', '国农科技', '世纪星源', '深振业A', '全新好'],
            'area': ['深圳', '深圳', '深圳', '深圳', '深圳', '深圳'],
            'industry': ['银行', '全国地产', '生物制药', '环境保护', '区域地产', '食品'],
            'full_name': ['平安银行股份有限公司', '万科企业股份有限公司', '国农科技股份有限公司', '世纪星源股份有限公司',
                          '深圳市振业(集团)股份有限公司', '深圳市全新好股份有限公司'],
            'enname': ['Ping An Bank Co., Ltd.', 'China Vanke Co., Ltd.',
                       'China National Agricultural Technology Co., Ltd.', 'Shijixingyuan Co., Ltd.',
                       'Shenzhen Zhenye(Group) Co., Ltd.', 'Shenzhen Quanxin Hao Co., Ltd.'],
            'cnspell': ['PAYH', 'WK', 'GNKJ', 'SJXY', 'SZYA', 'SXH'],
            'market': ['主板', '主板', '主板', '主板', '主板', '主板'],
            'exchange': ['SZSE', 'SZSE', 'SZSE', 'SZSE', 'SZSE', 'SZSE'],
            'curr_type': ['CNY', 'CNY', 'CNY', 'CNY', 'CNY', 'CNY'],
            'list_status': ['L', 'L', 'L', 'L', 'L', 'L'],
            'list_date': ['19910403', '19910129', '19951027', '19990602', '19921202', '19910809'],
            'delist_date': ['', '', '', '', '', ''],
            'is_hs': ['', '', '', '', '', ''],
        }
        stock_basic_df = pd.DataFrame(stock_basic)
        # 创建测试数据源的股票基础数据
        if not test_ds.table_data_exists('stock_basic'):
            test_ds.write_table_data(stock_basic_df, 'stock_basic')

        # 清空测试数据源中的所有相关表格数据
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if test_ds.table_data_exists(table):
                test_ds.drop_table_data(table)

        # 创建一个ID=1的账户
        new_account(user_name='test_user1', cash_amount=100000, data_source=test_ds)
        # 添加初始持仓
        get_or_create_position(account_id=1, symbol='000001.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000002.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000004.SZ', position_type='long', data_source=test_ds)
        get_or_create_position(account_id=1, symbol='000005.SZ', position_type='long', data_source=test_ds)
        update_position(position_id=1, data_source=test_ds, qty_change=200, available_qty_change=200, cost=10)
        update_position(position_id=2, data_source=test_ds, qty_change=200, available_qty_change=200, cost=10)
        update_position(position_id=3, data_source=test_ds, qty_change=300, available_qty_change=300, cost=10)
        update_position(position_id=4, data_source=test_ds, qty_change=200, available_qty_change=100, cost=10)

        self.ts = Trader(
                account_id=1,
                operator=operator,
                broker=broker,
                config=config,
                datasource=test_ds,
                debug=False,)
        self.ts.debug = True
        self.ts.renew_trade_log_file()

        self.tss = TraderShell(self.ts)

    def test_properties(self):

        tss = self.tss

        self.assertEqual(tss.trader, self.ts)
        self.assertEqual(tss.status, None)
        self.assertEqual(tss.watch_list, ['000300.SH',
                                          '000001.SZ',
                                          '000002.SZ',
                                          '000004.SZ',
                                          '000005.SZ',
                                          '000006.SZ',
                                          '000007.SZ'])

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

    def test_command_info(self):
        """ test info command"""
        tss = self.tss

        print('testing info command that runs normally and returns None')
        self.assertIsNone(tss.do_info(''))
        self.assertIsNone(tss.do_info('-d'))
        self.assertIsNone(tss.do_info('-s'))
        self.assertIsNone(tss.do_info('-d -s'))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_info('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_info('wrong_argument'))
        self.assertFalse(tss.do_info('-d -w wrong_optional_argument'))

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

        print('testing pool command that runs normally and returns None')
        self.assertIsNone(tss.do_pool(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_pool('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_pool('wrong_argument'))

    def test_command_watch(self):
        """ test watch command"""
        tss = self.tss

        print('testing watch command that runs normally and returns None')
        self.assertIsNone(tss.do_watch(''))

        print('testing add a new stock to watch list')
        self.assertIsNone(tss.do_watch('000002.SZ'))
        self.assertEqual(tss.watch_list, ['000001.SZ',
                                          '000002.SZ',
                                          '000004.SZ',
                                          '000005.SZ',
                                          '000006.SZ',
                                          '000007.SZ'])
        self.assertIsNone(tss.do_watch('000002.SZ'))
        self.assertEqual(tss.watch_list, ['000002.SZ',
                                          '000004.SZ',
                                          '000005.SZ',
                                          '000006.SZ',
                                          '000007.SZ'])

        print('testing remove a stock from watch list')
        self.assertIsNone(tss.do_watch('-r 000001.SH'))
        self.assertEqual(tss.watch_list, ['000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ'])
        self.assertIsNone(tss.do_watch('-r 000001.SH'))
        self.assertEqual(tss.watch_list, ['000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ'])

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
        # set live prices in trader for all assets for testing
        tss.trader.live_price = {
            '000001.SZ': 10.0,
            '000002.SZ': 20.0,
            '000004.SZ': 30.0,
            '000005.SZ': 40.0,
            '000006.SZ': 50.0,
            '000007.SZ': 60.0,
        }

        print('testing buy command that runs normally and returns None')
        self.assertIsNone(tss.do_buy('100 000001.SZ -p 10.0'))
        order = read_trade_order_detail(order_id=1, data_source=tss.trader.datasource)
        self.assertEqual(order['account_id'], 1)
        self.assertEqual(order['position'], 'long')
        self.assertEqual(order['symbol'], '000001.SZ')
        self.assertEqual(order['direction'], 'buy')
        self.assertEqual(order['qty'], 100)
        self.assertEqual(order['order_type'], 'market')
        self.assertEqual(order['price'], 10.0)
        self.assertIsNone(tss.do_buy('100 000001.SZ -p 30 -s long'))
        order = read_trade_order_detail(order_id=2, data_source=tss.trader.datasource)
        self.assertEqual(order['account_id'], 1)
        self.assertEqual(order['position'], 'long')
        self.assertEqual(order['symbol'], '000001.SZ')
        self.assertEqual(order['direction'], 'buy')
        self.assertEqual(order['qty'], 100)
        self.assertEqual(order['order_type'], 'market')
        self.assertEqual(order['price'], 30.0)
        print(f'testing buy command with no price given and use live price')
        print('trader live price is:', tss.trader.live_price)
        self.assertIsNone(tss.do_buy('100 000002.SZ'))
        order = read_trade_order_detail(order_id=3, data_source=tss.trader.datasource)
        self.assertEqual(order['account_id'], 1)
        self.assertEqual(order['position'], 'long')
        self.assertEqual(order['symbol'], '000002.SZ')
        self.assertEqual(order['direction'], 'buy')
        self.assertEqual(order['qty'], 100)
        self.assertEqual(order['order_type'], 'market')
        self.assertEqual(order['price'], 20.0)

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_buy('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_buy('no_qty 000001.SZ -p 10.0'))
        self.assertFalse(tss.do_buy('100 wrong_symbol -p 10.0'))
        self.assertFalse(tss.do_buy('100 000001.SZ -p 10.0 -s wrong_position'))
        self.assertFalse(tss.do_buy('100 000001.SZ -p -s long'))  # no price given
        self.assertFalse(tss.do_buy('-100 000001.SZ -p 10.0 -s long'))  # negative qty
        self.assertFalse(tss.do_buy('100 000001.SZ -p -10.0 -s long'))  # negative price
        self.assertFalse(tss.do_buy('100 000001.SZ -p 10.0 -s long -w wrong_argument'))
        self.assertFalse(tss.do_buy('11.2 000001.SZ -p 10.0 -s long'))  # qty not multiple of moq
        print(f'change moq to 0 and then test again')
        self.assertIsNone(tss.do_config('trade_batch_size -s 0'))
        self.assertIsNone(tss.do_buy('11.2 000001.SZ -p 10.0 -s long'))  # qty now accepted

    def test_command_sell(self):
        """ test sell command"""
        tss = self.tss
        # set live prices in trader for all assets for testing
        tss.trader.live_price = {
            '000001.SZ': 10.0,
            '000002.SZ': 20.0,
            '000004.SZ': 30.0,
            '000005.SZ': 40.0,
            '000006.SZ': 50.0,
            '000007.SZ': 60.0,
        }

        print('testing sell command that runs normally and returns None')
        self.assertIsNone(tss.do_sell('100 000001.SZ -p 10.0'))
        order = read_trade_order_detail(order_id=1, data_source=tss.trader.datasource)
        self.assertEqual(order['account_id'], 1)
        self.assertEqual(order['position'], 'long')
        self.assertEqual(order['symbol'], '000001.SZ')
        self.assertEqual(order['direction'], 'sell')
        self.assertEqual(order['qty'], 100)
        self.assertEqual(order['order_type'], 'market')
        self.assertEqual(order['price'], 10.0)
        self.assertIsNone(tss.do_sell('100 000001.SZ -p 30 -s long'))
        order = read_trade_order_detail(order_id=2, data_source=tss.trader.datasource)
        self.assertEqual(order['account_id'], 1)
        self.assertEqual(order['position'], 'long')
        self.assertEqual(order['symbol'], '000001.SZ')
        self.assertEqual(order['direction'], 'sell')
        self.assertEqual(order['qty'], 100)
        self.assertEqual(order['order_type'], 'market')
        self.assertEqual(order['price'], 30.0)
        print(f'testing sell command with no price given and use live price')
        print('trader live price is:', tss.trader.live_price)
        self.assertIsNone(tss.do_sell('100 000002.SZ'))
        order = read_trade_order_detail(order_id=3, data_source=tss.trader.datasource)
        self.assertEqual(order['account_id'], 1)
        self.assertEqual(order['position'], 'long')
        self.assertEqual(order['symbol'], '000002.SZ')
        self.assertEqual(order['direction'], 'sell')
        self.assertEqual(order['qty'], 100)
        self.assertEqual(order['order_type'], 'market')
        self.assertEqual(order['price'], 20.0)

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_sell('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_sell('no_qty 000001.SZ -p 10.0'))
        self.assertFalse(tss.do_sell('100 wrong_symbol -p 10.0'))
        self.assertFalse(tss.do_sell('100 000001.SZ -p 10.0 -s long'))
        self.assertFalse(tss.do_sell('100 000001.SZ -p -s long'))  # no price given
        self.assertFalse(tss.do_sell('-100 000001.SZ -p 10.0 -s long'))  # negative qty
        self.assertFalse(tss.do_sell('100 000001.SZ -p -10.0 -s long'))  # negative price

    def test_command_positions(self):
        """ test positions command"""
        tss = self.tss

        print('testing positions command that runs normally and returns None')
        self.assertIsNone(tss.do_positions(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_positions('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_positions('wrong_argument'))

    def test_command_overview(self):
        """ test overview command"""
        tss = self.tss

        print('testing overview command that runs normally and returns None')
        self.assertIsNone(tss.do_overview(''))
        self.assertIsNone(tss.do_overview('-d'))
        self.assertIsNone(tss.do_overview('-s'))
        self.assertIsNone(tss.do_overview('-d -s'))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_overview('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_overview('wrong_argument'))
        self.assertFalse(tss.do_overview('-d -w wrong_optional_argument'))

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
        test_ds = tss.trader.datasource

        # 添加测试交易订单以及交易结果
        print('Adding test trade orders and results...')
        self.stoppage = 0.1
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
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        2,
            'filled_qty':      100,
            'price':           70.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      200,
            'price':           80.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        4,
            'filled_qty':      400,
            'price':           89.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        5,
            'filled_qty':      500,
            'price':           100.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      100,
            'price':           78.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        6,
            'filled_qty':      200,
            'price':           69.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        7,
            'filled_qty':      200,
            'price':           31.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        time.sleep(self.stoppage)
        raw_trade_result = {
            'order_id':        9,
            'filled_qty':      300,
            'price':           91.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result=raw_trade_result, data_source=test_ds)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)
        # order 8 is canceled
        time.sleep(self.stoppage)
        process_account_delivery(account_id=1, data_source=test_ds, config=delivery_config)

        print('testing history command that runs normally and returns None')
        self.assertIsNone(tss.do_history(''))
        self.assertIsNone(tss.do_history('000001.SZ'))
        self.assertIsNone(tss.do_history('000002.SZ'))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_history('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_history('wrong_argument'))
        self.assertFalse(tss.do_history('000001.SZ -w wrong_optional_argument'))

    def test_command_orders(self):
        """ test orders command"""
        tss = self.tss

        # add testing orders to test data source
        print('Adding test trade orders and results...')
        self.stoppage = 0.1
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
                data_source=tss.trader.datasource,
        )
        # submit orders
        for order_id in order_ids:
            submit_order(order_id, tss.trader.datasource)

        # create order results
        delivery_config = {
            'cash_delivery_period':  0,
            'stock_delivery_period': 0,
        }
        # order 1 is filled
        raw_trade_result = {
            'order_id':        1,
            'filled_qty':      100,
            'price':           60.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, tss.trader.datasource)
        process_account_delivery(account_id=1, data_source=tss.trader.datasource, config=delivery_config)
        time.sleep(self.stoppage)
        # order 2 is filled
        raw_trade_result = {
            'order_id':        2,
            'filled_qty':      100,
            'price':           70.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, tss.trader.datasource)
        process_account_delivery(account_id=1, data_source=tss.trader.datasource, config=delivery_config)
        time.sleep(self.stoppage)
        # order 3 is partially-filled
        raw_trade_result = {
            'order_id':        3,
            'filled_qty':      200,
            'price':           80.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, tss.trader.datasource)
        process_account_delivery(account_id=1, data_source=tss.trader.datasource, config=delivery_config)
        time.sleep(self.stoppage)
        # order 4 is partially-filled
        raw_trade_result = {
            'order_id':        4,
            'filled_qty':      200,
            'price':           89.5,
            'transaction_fee': 5.0,
            'canceled_qty':    0.0,
        }
        process_trade_result(raw_trade_result, tss.trader.datasource)
        process_account_delivery(account_id=1, data_source=tss.trader.datasource, config=delivery_config)
        time.sleep(self.stoppage)
        # order 5 is canceled
        raw_trade_result = {
            'order_id':        5,
            'filled_qty':      0,
            'price':           0.0,
            'transaction_fee': 0.0,
            'canceled_qty':    500.0,
        }
        process_trade_result(raw_trade_result, tss.trader.datasource)
        time.sleep(self.stoppage)

        print('testing orders command that runs normally and returns None')
        print(f'\nprint all orders')
        self.assertIsNone(tss.do_orders(''))
        print(f'\nprint orders of 000001.SZ')
        self.assertIsNone(tss.do_orders('000001'))
        print(f'\nprint orders that are filled')
        self.assertIsNone(tss.do_orders('--status filled'))
        print(f'\nprint orders that are canceled')
        self.assertIsNone(tss.do_orders('-s canceled'))
        print(f'\nprint orders that are executed today')
        self.assertIsNone(tss.do_orders('--time today'))
        print(f'\nprint orders that are executed yesterday')
        self.assertIsNone(tss.do_orders('-t yesterday'))
        print(f'\nprint orders that are buy orders')
        self.assertIsNone(tss.do_orders('--type buy'))
        print(f'\nprint orders that are sell orders')
        self.assertIsNone(tss.do_orders('-y sell'))
        print(f'\nprint orders that are on the long side')
        self.assertIsNone(tss.do_orders('--side long'))
        print(f'\nprint orders that are on the short side')
        self.assertIsNone(tss.do_orders('-d short'))
        print(f'\nprint buy long orders of 000001.SZ that are filled today')
        self.assertIsNone(tss.do_orders('000001 --status filled -t today --type buy -d long'))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_orders('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_orders('wrong_argument'))
        self.assertFalse(tss.do_orders('000001 -w wrong_optional_argument'))
        self.assertFalse(tss.do_orders('000001 -t wrong_optional_argument'))

    def test_command_change(self):
        """ test change command"""
        tss = self.tss

        print('testing change command that runs normally and returns None')
        print('testing change quantity without price')
        position = get_position_by_id(1, tss.trader.datasource)
        self.assertEqual(position['qty'], 200)
        self.assertEqual(position['available_qty'], 200)
        self.assertEqual(position['cost'], 10)
        self.assertIsNone(tss.do_change('000001 --amount 100'))
        position = get_position_by_id(1, tss.trader.datasource)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 300)
        self.assertEqual(position['cost'], 10)
        self.assertIsNone(tss.do_change('000001 -a -100'))
        position = get_position_by_id(1, tss.trader.datasource)
        self.assertEqual(position['qty'], 200)
        self.assertEqual(position['available_qty'], 200)
        self.assertEqual(position['cost'], 10)
        print('testing reducing quantity exceeding holding qty')
        self.assertIsNone(tss.do_change('000001 -a -300'))  # reduce 300 out of 200 will leads to no change
        position = get_position_by_id(1, tss.trader.datasource)
        self.assertEqual(position['qty'], 200)
        self.assertEqual(position['available_qty'], 200)
        self.assertEqual(position['cost'], 10)
        print('testing add short side quantity')
        self.assertIsNone(tss.do_change('000001 -a 300 -s short'))  # 已经拥有000001多头仓位的同时不能拥有空头仓位
        with self.assertRaises(RuntimeError):
            get_position_by_id(5, tss.trader.datasource)
        # 必须首先将多头仓位将为0后才能添加空头仓位
        self.assertIsNone(tss.do_change('000001 -a -200'))
        self.assertIsNone(tss.do_change('000001 -a 200 -s short'))
        position_1 = get_position_by_id(1, tss.trader.datasource)
        position_5 = get_position_by_id(5, tss.trader.datasource)
        # 多头仓位已经为0，空头仓位200
        self.assertEqual(position_1['symbol'], '000001.SZ')
        self.assertEqual(position_1['position'], 'long')
        self.assertEqual(position_1['qty'], 0)
        self.assertEqual(position_1['available_qty'], 0)
        self.assertEqual(position_1['cost'], 0)

        self.assertEqual(position_5['symbol'], '000001.SZ')
        self.assertEqual(position_5['position'], 'short')
        self.assertEqual(position_5['qty'], 200)
        self.assertEqual(position_5['available_qty'], 200)
        self.assertEqual(position_5['cost'], 10)
        # clear short position of 000001 again
        self.assertIsNone(tss.do_change('000001 -a -200 -s short'))

        print('testing change quantity with price')
        self.assertIsNone(tss.do_change('000001 --amount 200 --price 10'))
        self.assertIsNone(tss.do_change('000001 --amount 200 --price 20'))
        position = get_position_by_id(1, tss.trader.datasource)
        self.assertEqual(position['qty'], 400)
        self.assertEqual(position['available_qty'], 400)
        self.assertEqual(position['cost'], 15)
        self.assertIsNone(tss.do_change('000001 -a -200 -p 10'))
        position = get_position_by_id(1, tss.trader.datasource)
        self.assertEqual(position['qty'], 200)
        self.assertEqual(position['available_qty'], 200)
        self.assertEqual(position['cost'], 20)
        print(f'testing change cash and available cashes')
        account = get_account(1, data_source=tss.trader.datasource)

        self.assertEqual(account['cash_amount'], 100000)
        self.assertEqual(account['available_cash'], 100000)
        self.assertEqual(account['total_invest'], 100000)
        self.assertIsNone(tss.do_change('--cash 10000'))
        account = get_account(1, data_source=tss.trader.datasource)
        self.assertEqual(account['cash_amount'], 110000)
        self.assertEqual(account['available_cash'], 110000)
        self.assertEqual(account['total_invest'], 110000)
        self.assertIsNone(tss.do_change('-c -10000'))
        account = get_account(1, data_source=tss.trader.datasource)
        self.assertEqual(account['cash_amount'], 100000)
        self.assertEqual(account['available_cash'], 100000)
        self.assertEqual(account['total_invest'], 100000)
        print('testing reducing cash amount exceeding on hand cash')
        self.assertIsNone(tss.do_change('-c -300000'))  # reducing 300k out of 100k will change nothing
        account = get_account(1, data_source=tss.trader.datasource)
        self.assertEqual(account['cash_amount'], 100000)
        self.assertEqual(account['available_cash'], 100000)
        self.assertEqual(account['total_invest'], 100000)

        print(f'testing change cash and position quantities in the same time')
        position = get_position_by_id(2, tss.trader.datasource)
        account = get_account(1, data_source=tss.trader.datasource)
        self.assertEqual(position['qty'], 200)
        self.assertEqual(position['available_qty'], 200)
        self.assertEqual(position['cost'], 10)
        self.assertEqual(account['cash_amount'], 100000)
        self.assertEqual(account['available_cash'], 100000)
        self.assertEqual(account['total_invest'], 100000)
        self.assertIsNone(tss.do_change('000002 --amount 300 --cash 10000 --price 20'))
        position = get_position_by_id(2, tss.trader.datasource)
        account = get_account(1, data_source=tss.trader.datasource)
        self.assertEqual(position['qty'], 500)
        self.assertEqual(position['available_qty'], 500)
        self.assertEqual(position['cost'], 16)
        self.assertEqual(account['cash_amount'], 110000)
        self.assertEqual(account['available_cash'], 110000)
        self.assertEqual(account['total_invest'], 110000)
        self.assertIsNone(tss.do_change('000002 -a -200 -c -10000 -p 10'))
        position = get_position_by_id(2, tss.trader.datasource)
        account = get_account(1, data_source=tss.trader.datasource)
        self.assertEqual(position['qty'], 300)
        self.assertEqual(position['available_qty'], 300)
        self.assertEqual(position['cost'], 20)
        self.assertEqual(account['cash_amount'], 100000)
        self.assertEqual(account['available_cash'], 100000)
        self.assertEqual(account['total_invest'], 100000)

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_change('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_change('wrong_argument'))
        self.assertFalse(tss.do_change('000001 -w wrong_optional_argument'))
        self.assertFalse(tss.do_change('000001 -t wrong_optional_argument'))
        self.assertFalse(tss.do_change('-a 100'))  # no symbol given
        self.assertFalse(tss.do_change('-p 100'))  # only price is given
        self.assertFalse(tss.do_change('-a 100 -p 100'))  # no symbol given
        self.assertFalse(tss.do_change('000100 -a 100'))  # symbol not in pool
        self.assertFalse(tss.do_change('000001 -a -100'))  # negative quantity
        self.assertFalse(tss.do_change('000001 -a not_a_number'))
        self.assertFalse(tss.do_change('000001 -a 100 -p not_a_number'))
        self.assertFalse(tss.do_change('000001 -a 100 -p -10'))  # negative price
        self.assertFalse(tss.do_change('000001 -a 100 -p 10 -c not_a_number'))
        self.assertFalse(tss.do_change('000001 -a 100 -p 10 -c -10'))  # negative cash

    def test_command_dashboard(self):
        """ test dashboard command"""
        tss = self.tss

        print('testing dashboard command that runs normally and returns True to exit the shell')
        self.assertTrue(tss.do_dashboard(''))
        self.assertTrue(tss.do_dashboard('--rewind 20'))
        self.assertTrue(tss.do_dashboard('-r 20'))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_dashboard('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_dashboard('wrong_argument'))
        self.assertFalse(tss.do_dashboard('-r not_an_int'))
        self.assertFalse(tss.do_dashboard('-r -10'))  # negative number
        self.assertFalse(tss.do_dashboard('-r 10_000'))  # too large number
        self.assertFalse(tss.do_dashboard('-w wrong_optional_argument'))

    def test_command_strategies(self):
        """ test strategies command"""
        tss = self.tss

        print('testing strategies command that runs normally and returns None')

        print(f'\n-----------------------\n'
              f'testing operator info get without detail')
        self.assertIsNone(tss.do_strategies(''))
        print(f'\n-----------------------\n'
              f'testing operator info get with detail')
        self.assertIsNone(tss.do_strategies('-d'))

        print(f'\n-----------------------\n'
              f'testing strategies info get by id without detail')
        self.assertIsNone(tss.do_strategies('dma'))
        self.assertIsNone(tss.do_strategies('macd'))

        print(f'\n-----------------------\n'
              f'testing strategies info get two ids without detail')
        self.assertIsNone(tss.do_strategies('macd dma'))

        print(f'\n-----------------------\n'
              f'testing strategies info get by id with detail')
        self.assertIsNone(tss.do_strategies('dma -d'))
        self.assertIsNone(tss.do_strategies('macd -d'))

        print(f'\n-----------------------\n'
              f'testing strategies info get two ids with detail')
        self.assertIsNone(tss.do_strategies('macd dma -d'))

        print('\ntesting setting pars to one and two strategies')
        self.assertEqual(tss.trader.operator['macd'].pars, (12, 26, 9))
        self.assertIsNone(tss.do_strategies('macd -s 35 25 55'))
        self.assertEqual(tss.trader.operator['macd'].pars, (35, 25, 55))
        self.assertEqual(tss.trader.operator['dma'].pars, (12, 26, 9))
        self.assertIsNone(tss.do_strategies('dma -s 35 25 55'))
        self.assertEqual(tss.trader.operator['dma'].pars, (35, 25, 55))
        self.assertIsNone(tss.do_strategies('dma macd -s 40 41 42 -s 43 44 45'))
        self.assertEqual(tss.trader.operator['dma'].pars, (40, 41, 42))
        self.assertEqual(tss.trader.operator['macd'].pars, (43, 44, 45))

        print('\ntesting setting blender to timing')
        self.assertIsNone(tss.do_strategies('-b s0*s1 -t close'))

        print(f'\ntesting getting help and returns False')
        self.assertFalse(tss.do_strategies('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_strategies('wrong_strategy'))
        self.assertFalse(tss.do_strategies('-w wrong_optional_argument'))
        self.assertFalse(tss.do_strategies('dma -s wrong par types'))
        self.assertFalse(tss.do_strategies('dma -s 1 2 3'))  # out of range pars
        self.assertFalse(tss.do_strategies('dma -s 44 44 44 44'))  # too many pars
        self.assertFalse(tss.do_strategies('dma macd -s 44 44 44'))  # value not match strategy
        self.assertFalse(tss.do_strategies('-d blender -s 44 44 44'))  # blender without timing
        self.assertFalse(tss.do_strategies('-d blender -t wrong_timing'))
        self.assertFalse(tss.do_strategies('-d wrong_blender -t wrong_timing'))

    def test_command_schedule(self):
        """ test schedule command"""
        tss = self.tss

        print('testing schedule command that runs normally and returns None')
        self.assertIsNone(tss.do_schedule(''))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_schedule('-h'))

        print('testing schedule command with wrong arguments and returns False')
        self.assertFalse(tss.do_schedule('wrong_argument'))

    def test_command_run(self):
        """ test run command"""
        tss = self.tss

        print('testing run command that runs normally and returns None')
        self.assertIsNone(tss.do_run('dma'))
        self.assertIsNone(tss.do_run('macd'))
        self.assertIsNone(tss.do_run('dma macd'))
        self.assertIsNone(tss.do_run('--task pre_open'))

        print(f'testing getting help and returns False')
        self.assertFalse(tss.do_run('-h'))

        print(f'testing run command with wrong arguments and returns False')
        self.assertFalse(tss.do_run(''))
        self.assertFalse(tss.do_run('wrong_argument'))
        self.assertFalse(tss.do_run('-- wrong task'))


if __name__ == '__main__':
    unittest.main()
