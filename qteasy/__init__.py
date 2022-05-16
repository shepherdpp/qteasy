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
import logging
from logging.handlers import TimedRotatingFileHandler

from .core import get_current_holdings, filter_stock_codes, filter_stocks, get_table_info
from .core import info, is_ready, configure, configuration, save_config, load_config, reset_config
from .core import run, get_basic_info
from .history import HistoryPanel, get_history_panel
from .history import dataframe_to_hp, stack_dataframes
from .operator import Operator
from .strategy import RuleIterator, GeneralStg, FactorSorter
from .visual import candle
from .built_in import *
from .finance import CashPlan, Cost
from .database import DataSource, find_history_data
from ._arg_validators import QT_CONFIG

from pathlib import Path

logger_core = logging.getLogger('core')
logger_core.setLevel(logging.DEBUG)
debug_handler = TimedRotatingFileHandler(filename='qteasy/log/qteasy.log', backupCount=3, when='midnight')
error_handler = logging.StreamHandler()
debug_handler.setLevel(logging.DEBUG)
error_handler.setLevel(logging.WARNING)
formatter = logging.Formatter('[%(asctime)s]:%(levelname)s - %(module)s -: %(message)s')
debug_handler.setFormatter(formatter)
logger_core.addHandler(debug_handler)
logger_core.addHandler(error_handler)

qt_local_configs = {}  # 存储本地配置文件的配置

# 解析qteasy的本地安装路径
QT_ROOT_PATH = str(Path('.').resolve()) + '/'
QT_CONFIG_FILE_INTRO = '# qteasy configuration file\n' \
                       '# following configurations will be loaded when initialize qteasy\n\n' \
                       '# example:\n' \
                       '# local_data_source = database\n\n'
# 读取configurations文件内容到config_lines列表中，如果文件不存在，则创建一个空文本文件
try:
    with open(QT_ROOT_PATH+'qteasy/qteasy.cnf') as f:
        config_lines = f.readlines()
        logger_core.info(f'read configuration file: {f.name}')
except FileNotFoundError as e:
    logger_core.warning(f'{e}\na new configuration file is created.')
    f = open(QT_ROOT_PATH + 'qteasy/qteasy.cnf', 'w')
    intro = QT_CONFIG_FILE_INTRO
    f.write(intro)
    f.close()
    config_lines = []  # 本地配置文件行
except Exception as e:
    logger_core.warning(f'{e}\nreading configuration file error, default configurations will be used')
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
        try:
            qt_local_configs[arg_name] = arg_value
            logger_core.info(f'qt configuration set: "{arg_name}" = {arg_value}')
        except Exception as e:
            logger_core.warning(f'{e}, invalid parameter: {arg_name} = {arg_value}')

# 读取tushare token，如果读取失败，抛出warning
try:
    TUSHARE_TOKEN = qt_local_configs['tushare_token']
    ts.set_token(TUSHARE_TOKEN)
    logger_core.info(f'tushare token set')
except Exception as e:
    logger_core.warning(f'{e}, tushare token was not loaded, features might not work properly!')

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
logger_core.info(f'local data source created: {QT_DATA_SOURCE}')

QT_TRADE_CALENDAR = QT_DATA_SOURCE.read_table_data('trade_calendar')
if not QT_TRADE_CALENDAR.empty:
    QT_TRADE_CALENDAR = QT_TRADE_CALENDAR
    logger_core.info(f'qteasy trade calendar created')
else:
    QT_TRADE_CALENDAR = None
    logger_core.warning(f'trade calendar can not be loaded, some of the trade day related functions may not work properly.'
                        f'\nrun "qt.QT_DATA_SOURCE.refill_data_source(\'trade_calendar\')" to '
                        f'download trade calendar data')

np.seterr(divide='ignore', invalid='ignore')
logger_core.info('qteasy loaded!')

QT_ERR_LOG_PATH = QT_ROOT_PATH + QT_CONFIG['error_log_file_path']
QT_TRADE_LOG_PATH = QT_ROOT_PATH + QT_CONFIG['trade_log_file_path']
