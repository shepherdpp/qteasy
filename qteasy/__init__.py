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
import logging
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from argparse import Namespace
from typing import Optional

import tushare as ts
import numpy as np

from qteasy.trade_recording import delete_account
from qteasy.qt_operator import Operator
from qteasy.visual import candle
from qteasy.parameter import Parameter

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
    get_kline,
    filter_stock_codes,
    filter_stocks,
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
    configure,
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
    DataType,
    StgData,
)

from qteasy._arg_validators import (
    QT_CONFIG,
    ConfigDict,
)


# qteasy版本信息
__version__ = '2.1.4'
version_info = Namespace(
        major=2,
        minor=1,
        patch=4,
        short=(2, 1),
        full=(2, 1, 4),
        string='2.1.4',
        tuple=('2', '1', '4'),
        releaselevel='beta',
)

# 解析qteasy的本地安装路径
QT_ROOT_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), os.pardir))
QT_ROOT_PATH = os.path.join(QT_ROOT_PATH, 'qteasy/')

QT_SYS_LOG_PATH = ''
QT_TRADE_LOG_PATH = ''

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
          f'https://qteasy.readthedocs.io/zh-cn/latest/tutorials/1-get-started.html'
    warnings.warn(msg, stacklevel=2)

# 读取其他本地配置属性，更新QT_CONFIG, 允许用户自定义参数存在
set_config(only_built_in_keys=False, **_qt_local_configs)

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
    warnings.warn(msg, stacklevel=2)

# 设置qteasy运行过程中忽略某些numpy计算错误报警
np.seterr(divide='ignore', invalid='ignore')


def _validate_path_string(path_setting: str, config_key: str) -> None:
    """ 校验路径配置字符串中是否包含非法字符，若存在则抛出 ValueError。

    通用规则：禁止 ASCII 控制字符（0x00-0x1F、0x7F）。
    Windows 下额外禁止 <>"|?*，且仅允许在第二位出现冒号（如 C:）。
    """
    if not isinstance(path_setting, str):
        raise ValueError(
            f'Path configuration "{config_key}" must be a string, got {type(path_setting).__name__}.'
        )
    for c in path_setting:
        if ord(c) < 32 or ord(c) == 127:
            raise ValueError(
                f'Invalid control character in configuration "{config_key}": '
                'path must not contain control characters.'
            )
    if os.name == 'nt':
        forbidden = set('<>"|?*')
        for i, c in enumerate(path_setting):
            if c in forbidden:
                raise ValueError(
                    f'Invalid character in configuration "{config_key}": "{c}" is not allowed in path.'
                )
            if c == ':':
                if not (i == 1 and len(path_setting) >= 2 and path_setting[0].isalpha()):
                    raise ValueError(
                        f'Invalid character in configuration "{config_key}": '
                        '":" only allowed as drive letter (e.g. C:).'
                    )


def _resolve_path(root: str, path_setting: str, config_key: str = 'path') -> str:
    """ 根据配置项解析为绝对路径：支持相对路径、绝对路径与 ~ 家目录路径。

    先做非法字符校验，再 expanduser，若为绝对路径则直接 normpath，否则相对 root 拼接。
    """
    _validate_path_string(path_setting, config_key)
    expanded = os.path.expanduser(path_setting)
    if os.path.isabs(expanded):
        return os.path.normpath(expanded)
    return os.path.normpath(os.path.join(root, expanded))


def _refresh_log_paths() -> None:
    """ 根据当前 QT_CONFIG 中的 sys_log_file_path、trade_log_file_path 刷新日志路径并创建目录。

    仅对上述两个配置项生效，不修改 local_data_file_path 或 QT_DATA_SOURCE。
    """
    global QT_SYS_LOG_PATH, QT_TRADE_LOG_PATH
    QT_SYS_LOG_PATH = _resolve_path(
        QT_ROOT_PATH, QT_CONFIG['sys_log_file_path'], 'sys_log_file_path'
    )
    QT_TRADE_LOG_PATH = _resolve_path(
        QT_ROOT_PATH, QT_CONFIG['trade_log_file_path'], 'trade_log_file_path'
    )
    os.makedirs(QT_SYS_LOG_PATH, exist_ok=True)
    os.makedirs(QT_TRADE_LOG_PATH, exist_ok=True)


def _rotate_trade_logs(base_path: str, keep_days: int) -> list[str]:
    """根据保留天数删除指定目录下的旧 trade_log / trade_summary 文件。

    优先从文件名中解析创建时间，格式参考 qt_operator 中的生成逻辑：
    trade_log_{operator_name}_%Y%m%d_%H%M%S.csv
    trade_summary_{operator_name}_%Y%m%d_%H%M%S.csv
    若解析失败，则退回使用文件修改时间近似作为创建时间。
    """
    from qteasy import QT_CONFIG  # 局部导入以避免循环引用

    if keep_days is None or keep_days <= 0:
        return []

    if not os.path.isdir(base_path):
        return []

    threshold = datetime.now() - timedelta(days=keep_days)
    removed_files: list[str] = []

    for name in os.listdir(base_path):
        full_path = os.path.join(base_path, name)
        if not os.path.isfile(full_path):
            continue
        if not (name.startswith('trade_log_') or name.startswith('trade_summary_') or name.startswith('value_curve_')):
            continue
        if not name.endswith('.csv'):
            continue

        created_time: Optional[datetime] = None

        try:
            # 解析文件名中的时间戳部分：{prefix}_{operator_name}_%Y%m%d_%H%M%S.csv
            stem = name[:-4]  # 去除 .csv
            parts = stem.split('_')
            if len(parts) >= 3:
                date_str, time_str = parts[-2], parts[-1]
                created_time = datetime.strptime(f'{date_str}_{time_str}', '%Y%m%d_%H%M%S')
        except Exception:
            created_time = None

        if created_time is None:
            # 解析失败时退回到 mtime
            try:
                created_time = datetime.fromtimestamp(os.path.getmtime(full_path))
            except Exception:
                continue

        if created_time < threshold:
            try:
                os.remove(full_path)
                removed_files.append(full_path)
            except Exception as e:
                # 仅记录 warning，不中断程序
                logging.getLogger('core').warning(
                    'Failed to remove old trade log file "%s": %s', full_path, e
                )

    if removed_files:
        logging.getLogger('core').info(
            'Rotated trade logs: %d files removed, keep_days=%s',
            len(removed_files),
            keep_days,
        )

    return removed_files


def _auto_rotate_trade_logs() -> None:
    """在模块初始化阶段，根据配置自动对当前 trade_log 目录做一次轮换删除。"""
    global QT_TRADE_LOG_PATH

    keep_days = QT_CONFIG.get('trade_log_keep_days', 0)
    if keep_days is None or (isinstance(keep_days, int) and keep_days <= 0):
        return

    _rotate_trade_logs(QT_TRADE_LOG_PATH, int(keep_days))


def rotate_trade_logs(days: Optional[int] = None) -> None:
    """手动触发 trade_log / trade_summary 轮换删除。

    Parameters
    ----------
    days : int or None
        若为 None，则使用全局配置 trade_log_keep_days；
        若为正整数，则以该值作为本次删除的保留天数（不修改全局配置）。
    """
    global QT_TRADE_LOG_PATH

    if days is None:
        keep_days = QT_CONFIG.get('trade_log_keep_days', 0)
    else:
        if not isinstance(days, int):
            raise ValueError(f'Parameter "days" must be an integer or None, got {type(days).__name__}.')
        keep_days = days

    if keep_days is None or (isinstance(keep_days, int) and keep_days <= 0):
        return

    _rotate_trade_logs(QT_TRADE_LOG_PATH, int(keep_days))


# 设置qteasy回测交易报告以及错误报告的存储路径（支持热修改，见 configure 挂钩）
_refresh_log_paths()
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
# 根据 QT_CONFIG['log_level'] 设置日志等级，默认 INFO
_log_level_name = str(QT_CONFIG.get('log_level', 'INFO')).upper()
_log_level_value = getattr(logging, _log_level_name, logging.INFO)
logger_core.setLevel(_log_level_value)

# 在 logger 初始化完成后，根据配置自动做一次 trade_log 轮换
_auto_rotate_trade_logs()
logger_core.propagate = False

logger_core.info('qteasy loaded!')

# 检查当前python的版本信息，打印相关的warning信息
py_version = sys.version_info
py_ver_major = py_version.major
py_ver_minor = py_version.minor

# qteasy的全局常量
# 运行模式常量
LIVE_TRADE_MODE = 0
LIVE_MODE = 0
BACKTEST_MODE = 1
OPTIMIZE_MODE = 2
OPTI_MODE = 2
OPTIMIZATION_MODE = 2
PREDICT_MODE = 3
PREDICTION_MODE = 3

__all__ = [
    'run', 'set_config', 'get_configurations', 'get_config', 'view_config_files',
    'info', 'is_ready', 'configure', 'configuration', 'save_config', 'load_config', 'reset_config',
    'get_basic_info', 'get_stock_info', 'get_data_overview', 'refill_data_source',
    'get_history_data', 'filter_stock_codes', 'filter_stocks', 'start_up_config', 'Parameter',
    'get_table_info', 'get_table_overview', 'get_start_up_settings', 'find_history_data', 'DataType', 'StgData',
    'HistoryPanel', 'dataframe_to_hp', 'stack_dataframes', 'start_up_settings', 'update_start_up_setting', 'get_kline',
    'Operator', 'BaseStrategy', 'RuleIterator', 'GeneralStg', 'FactorSorter', 'remove_start_up_setting',
    'built_ins', 'built_in_list', 'built_in_strategies', 'get_built_in_strategy',
    'candle', 'CashPlan', 'set_cost', 'update_cost', 'DataSource', 'find_history_data',
    'QT_TRADE_CALENDAR', 'QT_TRADE_LOG_PATH', 'QT_ROOT_PATH', 'QT_SYS_LOG_PATH',
    'QT_DATA_SOURCE', 'QT_CONFIG', 'utilfuncs', 'QT_CONFIG', 'ConfigDict', '__version__', 'version_info',
    'logger_core', 'live_trade_accounts', 'delete_account', 'LIVE_TRADE_MODE', 'LIVE_MODE', 'BACKTEST_MODE',
    'OPTIMIZE_MODE', 'OPTI_MODE', 'OPTIMIZATION_MODE', 'PREDICT_MODE', 'PREDICTION_MODE',
]
