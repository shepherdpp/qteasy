# coding=utf-8
# ======================================
# File: akshare_refill_minimal.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-06-01
# Desc:
#   使用 AKShare 通道下载单表 stock_daily 的最小示例。
#   需要联网并已安装 akshare：pip install akshare
# ======================================

import os
import sys

sys.path.insert(0, os.path.abspath('../'))


if __name__ == '__main__':
    import qteasy as qt

    print('\n[akshare_refill_minimal] 使用 channel=akshare 下载 stock_daily（短日期窗）')
    ds = qt.DataSource()
    print(' data_source:', ds)

    # 仅下载两只股票、短区间，便于快速验证 AKShare 通道（需联网）
    qt.refill_data_source(
        tables='stock_daily',
        channel='akshare',
        data_source=ds,
        shares='000001.SZ,600000.SH',
        start_date='20240101',
        end_date='20240110',
    )

    sample = ds.read_table_data(
        'stock_daily',
        shares='000001.SZ',
        start='20240101',
        end='20240110',
    )
    print('\n[akshare_refill_minimal] 读回样本行数:', len(sample))
    print(sample.head())
