# coding=utf-8

from .core import *
from .history import *
from .operator import *
from .strategy import *
from .visual import *
from .built_in import *
from .finance import *

# TODO: 仅需要导入用户可能会用到的类或函数即可，不需要导入所有的函数

# TODO: *************************************************************
# TODO: *                 GRAND TODO PLAN 2021                      *
# TODO: * (1): Function intro, search and setting validation:       *
# TODO: *      内置功能查询、介绍及输入检查：                             *
# TODO: *       实现基本的帮助功能，实现大部分基本功能的功能介绍和查询         *
# TODO: *       在运行策略之前显示关键参数，并检查参数是否存在逻辑问题
# TODO: *
# TODO: * (2): Built-in strategy base
# TODO: *      更完善的内置策略：
# TODO: *       内置策略包含果仁网等常规量化投资网站上包含的基本投资策略
# TODO: *       增加利用指数择时的指数择时策略
# TODO: *
# TODO: * (3): Advanced strategy evaluation
# TODO: *      增强的策略优化结果评价：
# TODO: *       多重历史数据区间的复合回测性能评价
# TODO: *       通过生成伪历史数据进行蒙特卡洛模拟评价
# TODO: *
# TODO: * (4): Run parameter management and loggings
# TODO: *      优化运行参数管理及运行日志记录：
# TODO: *       使用参数表和参数字典的形式管理运行参数，并统一参数验证
# TODO: *       使用loggings模块生成策略运行日志
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

print(f'Module qteasy has been loaded successfully!, version: 0.1')
print('tushare version:', ts.__version__)


TUSHARE_TOKEN = '14f96621db7a937c954b1943a579f52c09bbd5022ed3f03510b77369'
ts.set_token(TUSHARE_TOKEN)

print('tushare token set!')