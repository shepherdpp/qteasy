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
import sys

from threading import Thread

import qteasy
from qteasy.trader import TaskScheduler
from qteasy.broker import QuickBroker


class TestTrader(unittest.TestCase):
    def test_class(self):
        """Test class TaskScheduler"""
        operator = qteasy.Operator(strategies=['macd', 'dma'])
        broker = QuickBroker()
        config = {
            'market_open_time_am': '09:30:00',
            'market_close_time_pm': '15:30:00',
            'market_open_time_pm': '13:00:00',
            'market_close_time_am': '11:30:00',
            'exchange': 'SSE',
        }
        datasource = qteasy.QT_DATA_SOURCE
        ts = TaskScheduler(1, operator, broker, config, datasource)
        self.assertIsInstance(ts, TaskScheduler)
        Thread(target=ts.run).start()
        time.sleep(1)
        sys.stdout.write(f'current status: {ts.status}')
        ts.add_task('start')
        time.sleep(10)
        sys.stdout.write(f'current status: {ts.status}')

    def test_run_task(self):
        """Test function run_task"""
        operator = qteasy.Operator(strategies=['macd', 'dma'])
        broker = QuickBroker()
        config = {
            'market_open_time_am': '09:30:00',
            'market_close_time_pm': '15:30:00',
            'market_open_time_pm': '13:00:00',
            'market_close_time_am': '11:30:00',
            'exchange': 'SSE',
        }
        datasource = qteasy.QT_DATA_SOURCE
        ts = TaskScheduler(1, operator, broker, config, datasource)
        ts.run_task('open_market')


if __name__ == '__main__':
    unittest.main()

