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
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('sleep')
        time.sleep(5)
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('wakeup')
        time.sleep(5)
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('pause')
        time.sleep(5)
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('resume')
        time.sleep(5)
        print(f'\ncurrent status: {ts.status}')
        ts.add_task('stop')
        time.sleep(5)
        print(f'\ncurrent status: {ts.status}')


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
        self.assertIsInstance(ts, TaskScheduler)
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


if __name__ == '__main__':
    unittest.main()

