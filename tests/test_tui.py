# coding=utf-8
# ======================================
# File:     test_tui.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-04-09
# Desc:
#   Unittest for the TUI
# ======================================

import unittest

import qteasy.trader
from qteasy import Operator, DataSource
from qteasy.trader_tui import TraderApp
from qteasy.broker import SimulatorBroker


class TestTUI(unittest.TestCase):

    def setUp(self) -> None:
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
        data_test_dir = '../qteasy/data_test/'
        # 创建一个专用的测试数据源，以免与已有的文件混淆，不需要测试所有的数据源，因为相关测试在test_datasource中已经完成
        test_ds = DataSource('file', file_type='csv', file_loc=data_test_dir)

        self.trader = qteasy.trader.Trader(
                account_id=1,
                operator=operator,
                broker=broker,
                config=config,
                datasource=test_ds,
        )

    def test_action_toggle_dark(self):
        ''' test action_toggle_dark '''
        trader = self.trader
        app = TraderApp(trader=trader)
        app.action_toggle_dark()
        self.assertEqual(app.dark, False)
        app.action_toggle_dark()
        self.assertEqual(app.dark, True)


if __name__ == '__main__':
    # unittest.main()
    pass
