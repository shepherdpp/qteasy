# coding=utf-8
# ======================================
# File:     test.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-11
# Desc:
#   QTEASY:
#   A fast and easy-to-use quant-investment
#   strategy research tool kit.
# ======================================

import tushare as ts

from .core import get_current_holdings, get_stock_pool
from .core import info, is_ready, configure, configuration
from .core import run, get_basic_info
from .history import HistoryPanel
from .history import csv_to_hp, hdf_to_hp, dataframe_to_hp, stack_dataframes
from .operator import Operator
from .strategy import RollingTiming, SimpleTiming, SimpleSelecting, FactoralSelecting
from .visual import candle
from .built_in import *
from .finance import CashPlan, Cost
from .database import DataSource
from ._arg_validators import QT_CONFIG
from warnings import warn

from pathlib import Path

qt_local_configs = {}  # 存储本地配置文件的配置

# 解析qteasy的本地安装路径
QT_ROOT_PATH = str(Path('.').resolve()) + '/'
# 读取configurations文件内容到config_lines列表中，如果文件不存在，则创建一个空文本文件
try:
    with open(QT_ROOT_PATH+'qteasy/qteasy.cnf') as f:
        config_lines = f.readlines()
except FileNotFoundError as e:
    print(f'{e}\na new configuration file is created.')
    f = open(QT_ROOT_PATH + 'qteasy/qteasy.cnf', 'w')
    intro = '# qteasy configuration file\n' \
            '# following configurations will be loaded when initialize qteasy\n\n' \
            '# example:\n' \
            '# local_data_source = database\n\n'
    f.write(intro)
    f.close()
    config_lines = []  # 本地配置文件行
except Exception as e:
    print(f'{e}\nreading configuration file error, default configurations will be used')
    config_lines = []

# 解析config_lines列表，依次读取所有存储的属性，所有属性存储的方式为：
# config = value
for line in config_lines:
    if line[0] == '#':  # 忽略注释行
        continue
    line = line.split('=')
    if len(line) == 2:
        arg_name = line[0].strip()
        arg_value = line[1].strip()
        qt_local_configs[arg_name] = arg_value

# 读取tushare token，如果读取失败，抛出warning
try:
    TUSHARE_TOKEN = qt_local_configs['tushare_token']
    ts.set_token(TUSHARE_TOKEN)
except Exception as e:
    warn(f'{e}, tushare token was not loaded, features might not work properly!',
         RuntimeWarning)

# 读取其他本地配置属性，更新QT_CONFIG
configure(**qt_local_configs)

# 建立默认的本地数据源
QT_DATA_SOURCE = DataSource(
        source_type=QT_CONFIG['local_data_source'],
        file_type=QT_CONFIG['local_data_file_type'],
        file_loc=QT_CONFIG['local_data_file_path'],
        host=QT_CONFIG['local_db_host'],
        port=QT_CONFIG['local_db_port'],
        user=QT_CONFIG['local_db_user'],
        password=QT_CONFIG['local_db_password'],
        db=QT_CONFIG['local_db_name']
)

QT_TRADE_CALENDAR = QT_DATA_SOURCE.read_table_data('trade_calendar')
if not QT_TRADE_CALENDAR.empty:
    QT_TRADE_CALENDAR = QT_TRADE_CALENDAR
else:
    QT_TRADE_CALENDAR = None
    print(f'trade calendar can not be loaded, some of the trade day related functions may not work properly.'
          f'\nrun "qt.QT_DATA_SOURCE.refill_data_source(\'trade_calendar\')" to '
          f'download trade calendar data')

np.seterr(divide='ignore', invalid='ignore')


