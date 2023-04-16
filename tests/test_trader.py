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
from qteasy.trader import Trader
from qteasy.broker import QuickBroker


class TestTrader(unittest.TestCase):
    def test_class(self):
        """Test class Trader"""
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
        ts = Trader(1, operator, broker, config, datasource)
        self.assertIsInstance(ts, Trader)
        Thread(target=ts.run).start()
        time.sleep(1)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('sleep')
        time.sleep(1)
        self.assertEqual(ts.status, 'sleeping')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')  # should be ignored
        time.sleep(1)
        self.assertEqual(ts.status, 'sleeping')
        ts.add_task('wakeup')
        time.sleep(1)
        self.assertEqual(ts.status, 'running')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')
        time.sleep(1)
        self.assertEqual(ts.status, 'paused')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('sleep')  # should be ignored
        time.sleep(1)
        self.assertEqual(ts.status, 'paused')
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('resume')
        time.sleep(1)
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('stop')
        time.sleep(1)
        print(f'\ncurrent status: {ts.status}')

        raise NotImplementedError('TestTrader.test_class not completed')

    def test_run_status_tasks(self):
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
        ts = Trader(1, operator, broker, config, datasource)
        self.assertIsInstance(ts, Trader)
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'running')
        ts.run_task('stop')
        self.assertEqual(ts.status, 'stopped')
        ts.run_task('start')
        self.assertEqual(ts.status, 'running')
        ts.run_task('sleep')
        self.assertEqual(ts.status, 'sleeping')
        ts.run_task('wakeup')
        self.assertEqual(ts.status, 'running')
        ts.run_task('pause')
        self.assertEqual(ts.status, 'paused')
        ts.run_task('resume')
        self.assertEqual(ts.status, 'running')

    def test_run_info_tasks(self):
        """ running tasks that retrieve trader and account information"""
        raise NotImplementedError

    def test_run_strategy(self):
        """ running task that runs strategy"""
        raise NotImplementedError


if __name__ == '__main__':
    unittest.main()

