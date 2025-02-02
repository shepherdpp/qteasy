# coding=utf-8
# ======================================
# Package:  qteasy
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-11
# Desc:
# QTEASY:
#  A fast and easy-to-use quant-investment
#  strategy research tool kit.
# ======================================

import os
import sys
import warnings

import tushare as ts
import numpy as np
import logging
from logging.handlers import TimedRotatingFileHandler
from argparse import Namespace

from qteasy.trade_recording import delete_account
from qteasy.qt_operator import Operator
from qteasy.visual import candle

from qteasy.core import (
    run,
    info,
    is_ready,
    configure,
    get_basic_info,
    get_stock_info,
    get_data_overview,
    refill_data_source,
    get_history_data,
    filter_stock_codes,
    filter_stocks,
    reconnect_ds,
    get_table_info,
    get_table_overview,
    live_trade_accounts,
)

from qteasy.utilfuncs import (
    is_float_like,
    is_integer_like,
)
from qteasy.configure import (
    set_config,
    get_configurations,
    get_config,
    view_config_files,
    get_start_up_settings,
    configuration,
    save_config,
    load_config,
    reset_config,
    _parse_start_up_config_lines,
    start_up_settings,
    update_start_up_setting,
    remove_start_up_setting,
    _read_start_up_file,
)

from qteasy.history import (
    HistoryPanel,
    dataframe_to_hp,
    stack_dataframes,
)

from qteasy.strategy import (
    BaseStrategy,
    RuleIterator,
    GeneralStg,
    FactorSorter,
)

from qteasy.built_in import (
    built_ins,
    built_in_list,
    built_in_strategies,
    get_built_in_strategy,
    built_in_doc,
)


from qteasy.finance import (
    CashPlan,
    set_cost,
    update_cost,
)

from qteasy.database import (
    DataSource,
    # find_history_data,
)

from qteasy.datatypes import (
    find_history_data,
)

from qteasy._arg_validators import (
    QT_CONFIG,
    ConfigDict,
)


# qteasy版本信息
__version__ = '1.4.0'
version_info = Namespace(
        major=1,
        minor=4,
        patch=0,
        short=(1, 4),
        full=(1, 4, 0),
        string='1.4.0',
        tuple=('1', '4', '0'),
        releaselevel='beta',
)

# 解析qteasy的本地安装路径
QT_ROOT_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
QT_ROOT_PATH = os.path.join(QT_ROOT_PATH, 'qteasy/')

# 准备从本地配置文件中读取预先存储的qteasy配置
_qt_local_configs = {}

# 读取start up configurations文件内容到config_lines列表中，如果文件不存在，则创建一个空文本文件
_config_lines = _read_start_up_file(os.path.join(QT_ROOT_PATH, 'qteasy.cfg'))

# 解析config_lines列表，依次读取所有存储的属性，所有属性存储的方式为：
start_up_config = _parse_start_up_config_lines(config_lines=_config_lines)

_qt_local_configs.update(start_up_config)

# 读取tushare token，如果读取失败，抛出warning
try:
    TUSHARE_TOKEN = _qt_local_configs['tushare_token']
    ts.set_token(TUSHARE_TOKEN)
except Exception as e:
    msg = f'Failed Loading tushare_token, configure it in qteasy.cfg:\n' \
            f'tushare_token = your_token\n' \
            f'for more information, check qteasy tutorial: ' \
            f'https://qteasy.readthedocs.io/zh/latest/tutorials/1-get-started.html'
    warnings.warn(msg)

# 读取其他本地配置属性，更新QT_CONFIG, 允许用户自定义参数存在
configure(only_built_in_keys=False, **_qt_local_configs)

# 连接默认的本地数据源
QT_DATA_SOURCE = DataSource(
        source_type=QT_CONFIG['local_data_source'],
        file_type=QT_CONFIG['local_data_file_type'],
        file_loc=QT_CONFIG['local_data_file_path'],
        host=QT_CONFIG['local_db_host'],
        port=QT_CONFIG['local_db_port'],
        user=QT_CONFIG['local_db_user'],
        password=QT_CONFIG['local_db_password'],
        db_name=QT_CONFIG['local_db_name']
)

# 初始化默认交易日历
QT_TRADE_CALENDAR = QT_DATA_SOURCE.read_table_data('trade_calendar')
if not QT_TRADE_CALENDAR.empty:
    QT_TRADE_CALENDAR = QT_TRADE_CALENDAR
else:
    QT_TRADE_CALENDAR = None
    msg = 'trade calendar is not loaded, some utility functions may not work properly, ' \
            'to download trade calendar, run \n"qt.refill_data_source(tables=\'trade_calendar\')"'
    warnings.warn(msg)

# 设置qteasy运行过程中忽略某些numpy计算错误报警
np.seterr(divide='ignore', invalid='ignore')

# 设置qteasy回测交易报告以及错误报告的存储路径
QT_SYS_LOG_PATH = os.path.join(QT_ROOT_PATH, QT_CONFIG['sys_log_file_path'])  # 系统日志存储路径
QT_TRADE_LOG_PATH = os.path.join(QT_ROOT_PATH, QT_CONFIG['trade_log_file_path'])  # 交易记录存储路径，包括回测和实盘交易

# 设置系统日志以及交易日志的存储路径，如果路径不存在，则新建一个文件夹
os.makedirs(QT_SYS_LOG_PATH, exist_ok=True)
os.makedirs(QT_TRADE_LOG_PATH, exist_ok=True)
# 设置loggings，创建logger
debug_handler = logging.handlers.TimedRotatingFileHandler(filename=os.path.join(QT_SYS_LOG_PATH, 'qteasy.log'),
                                                          backupCount=3, when='midnight')
error_handler = logging.StreamHandler()
debug_handler.setLevel(logging.DEBUG)
error_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('[%(asctime)s]:%(levelname)s - %(module)s -: %(message)s')
debug_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)
# 创建两个logger，一个是正常运行(回测、优化等）的logger，另一个是实盘运行logger
logger_core = logging.getLogger('core')
logger_core.addHandler(debug_handler)
logger_core.addHandler(error_handler)
logger_core.setLevel(logging.INFO)
logger_core.propagate = False

logger_core.info('qteasy loaded!')

# 检查当前python的版本信息，打印相关的warning信息
py_version = sys.version_info
py_ver_major = py_version.major
py_ver_minor = py_version.minor

__all__ = [
    'run', 'set_config', 'get_configurations', 'get_config', 'view_config_files',
    'info', 'is_ready', 'configure', 'configuration', 'save_config', 'load_config', 'reset_config',
    'get_basic_info', 'get_stock_info', 'get_data_overview', 'refill_data_source',
    'get_history_data', 'filter_stock_codes', 'filter_stocks', 'start_up_config',
    'reconnect_ds', 'get_table_info', 'get_table_overview', 'get_start_up_settings',
    'HistoryPanel', 'dataframe_to_hp', 'stack_dataframes', 'start_up_settings', 'update_start_up_setting',
    'Operator', 'BaseStrategy', 'RuleIterator', 'GeneralStg', 'FactorSorter', 'remove_start_up_setting',
    'built_ins', 'built_in_list', 'built_in_strategies', 'get_built_in_strategy',
    'candle', 'CashPlan', 'set_cost', 'update_cost', 'DataSource', 'find_history_data',
    'QT_TRADE_CALENDAR', 'QT_TRADE_LOG_PATH', 'QT_ROOT_PATH', 'QT_SYS_LOG_PATH',
    'QT_DATA_SOURCE', 'QT_CONFIG', 'utilfuncs', 'QT_CONFIG', 'ConfigDict', '__version__', 'version_info',
    'logger_core', 'live_trade_accounts', 'delete_account',
]
