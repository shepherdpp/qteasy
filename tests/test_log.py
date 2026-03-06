# coding=utf-8
# ======================================
# File:     test_log.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all qteasy log related
#   functionalities, including trade_log
#   rotation feature.
# ======================================

import os
import tempfile
import time
import unittest
from datetime import datetime, timedelta


import qteasy as qt


class TestLog(unittest.TestCase):

    def test_rotate_trade_logs_by_filename_timestamp(self):
        """基于文件名时间戳删除超期 trade_log / trade_summary 文件。"""
        print('\n[TestRotateLogsByFilename] 使用文件名中的时间戳判断是否过期')

        tmp_dir = tempfile.mkdtemp()

        # 构造两个不同日期的文件名：一个在保留期外，一个在保留期内
        now = datetime.now()
        old_ts = now - timedelta(days=40)
        recent_ts = now - timedelta(days=10)

        old_name = f"trade_log_testop_{old_ts.strftime('%Y%m%d_%H%M%S')}.csv"
        recent_name = f"trade_summary_testop_{recent_ts.strftime('%Y%m%d_%H%M%S')}.csv"

        old_path = os.path.join(tmp_dir, old_name)
        recent_path = os.path.join(tmp_dir, recent_name)

        with open(old_path, 'w', encoding='utf-8') as f:
            f.write('old\n')
        with open(recent_path, 'w', encoding='utf-8') as f:
            f.write('recent\n')

        # 使用 30 天保留期：old 应被删除，recent 应保留
        print(' tmp_dir:', tmp_dir)
        print(' files before rotation:', os.listdir(tmp_dir))

        original_path = qt.QT_TRADE_LOG_PATH
        try:
            qt.QT_TRADE_LOG_PATH = tmp_dir
            qt.rotate_trade_logs(days=30)
        finally:
            qt.QT_TRADE_LOG_PATH = original_path

        remaining = sorted(os.listdir(tmp_dir))
        print(' files after rotation:', remaining)

        self.assertFalse(os.path.exists(old_path))
        self.assertTrue(os.path.exists(recent_path))

    def test_rotate_trade_logs_fallback_to_mtime(self):
        """文件名无法解析时间戳时退回到 mtime 判断。"""
        print('\n[TestRotateLogsByMtime] 文件名不可解析时使用 mtime 近似创建时间')

        tmp_dir = tempfile.mkdtemp()

        invalid_name = "trade_log_invalid_name.csv"
        invalid_path = os.path.join(tmp_dir, invalid_name)
        with open(invalid_path, 'w', encoding='utf-8') as f:
            f.write('invalid\n')

        # 人为把 mtime 调整到 40 天前
        old_time = time.time() - 40 * 24 * 3600
        os.utime(invalid_path, (old_time, old_time))

        print(' tmp_dir:', tmp_dir)
        print(' files before rotation:', os.listdir(tmp_dir))

        original_path = qt.QT_TRADE_LOG_PATH
        try:
            qt.QT_TRADE_LOG_PATH = tmp_dir
            qt.rotate_trade_logs(days=30)
        finally:
            qt.QT_TRADE_LOG_PATH = original_path

        remaining = os.listdir(tmp_dir)
        print(' files after rotation:', remaining)

        self.assertFalse(os.path.exists(invalid_path))


if __name__ == '__main__':
    unittest.main()
