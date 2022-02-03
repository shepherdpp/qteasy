# coding=utf-8

import tushare as ts

from .core import get_current_holdings, get_stock_pool
from .core import info, is_ready, configure, configuration
from .core import run
from .history import HistoryPanel
from .history import csv_to_hp, hdf_to_hp, dataframe_to_hp, stack_dataframes
from .operator import Operator
from .strategy import RollingTiming, SimpleTiming, SimpleSelecting, FactoralSelecting
from .visual import candle, ohlc, renko
from .built_in import *
from .finance import CashPlan, Cost
from .database import DataSource
from ._arg_validators import QT_CONFIG
from warnings import warn

from pathlib import Path

# TODO: 仅需要导入用户可能会用到的类或函数即可，不需要导入所有的函数

# TODO: *************************************************************
# TODO: *                 GRAND TODO PLAN 2021
# TODO: * (1): Function intro, search and setting validation:
# TODO: *      内置功能查询、介绍及输入检查：
# TODO: *       实现基本的帮助功能，实现大部分基本功能的功能介绍和查询
# TODO: *       在运行策略之前显示关键参数，并检查参数是否存在逻辑问题
# TODO: *
# TODO: * (2): Complete Examples 
# TODO: *      完整的示例文件：
# TODO: *       全面介绍QTEASY的使用方法以及所有的内置策略的回测结果
# TODO: *
# TODO: * (3): Upgrated operation and strategy structure
# TODO: *      升级的运行和策略结构：
# TODO: *       多重历史数据区间的复合回测性能评价
# TODO: *       通过生成伪历史数据进行蒙特卡洛模拟评价
# TODO: *
# TODO: * (4): Create and Save Run Logs:
# TODO: *      生成并保存运行日志,
# TODO: *       使用DataFrame表格形式保存运行日志并开通保存日志功能
# TODO: *
# TODO: * (5): Advanced History data interface and Database
# TODO: *      统一化历史数据读取接口，本地数据通过数据库管理：
# TODO: *       统一历史数据接口，为以后扩展到兼容其他的历史数据接口作准备
# TODO: *       使用sqlite或mysql管理本地数据库，将本地数据存储在数据库中
# TODO: *
# TODO: * (6): pip installable package
# TODO: *      生成pip安装包：
# TODO: *       生成pip安装包
# TODO: *       完成说明文档
# TODO: *
# TODO: ************************************************************

qt_local_configs = {}  # 存储本地配置文件的配置

# 解析qteasy的本地安装路径
QT_ROOT_PATH = str(Path('.').resolve()) + '/'
# 读取configurations文件内容到config_lines列表中，如果文件不存在，则创建一个空文本文件
try:
    with open(QT_ROOT_PATH+'qteasy/configurations.txt') as f:
        config_lines = f.readlines()
except:
    # 新建文件：
    f = open(QT_ROOT_PATH + 'qteasy/configurations.txt', 'w')
    f.close()
    config_lines = []  # 本地配置文件行

# 解析config_lines列表，依次读取所有存储的属性，所有属性存储的方式为：
# config = value
for line in config_lines:
    line = line.split('=')
    if len(line) == 2:
        arg_name = line[0].strip()
        arg_value = line[1].strip()
        qt_local_configs[arg_name] = arg_value

# 读取tushare token，如果读取失败，抛出warning
try:
    TUSHARE_TOKEN = qt_local_configs['tushare_token']
    ts.set_token(TUSHARE_TOKEN)
except:
    warn('tushare token was not loaded, features might not work properly!',
         RuntimeWarning)

# 读取其他本地配置属性，更新QT_CONFIG
configure(**qt_local_configs)

np.seterr(divide='ignore', invalid='ignore')


