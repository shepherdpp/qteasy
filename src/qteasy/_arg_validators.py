# coding=utf-8
# ======================================
# File:     _arg_validators.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-10-09
# Desc:
#   Global level parameters and settings
#   of qteasy.
# ======================================

import pandas as pd
import numpy as np
import datetime
import warnings


class ConfigDict(dict):
    """ 继承自dict的一个类，用于构造qteasy的参数表字典对象
    参数字典比dict多出一个功能，即通过属性来访问字典的键值，提供访问便利性
    即：
    config_key.attr = config_key['attr']

    Methods
    -------
    copy()
        返回一个参数字典的深拷贝
    """

    def __init__(self, *args, **kwargs):
        """ 参数字典的初始化函数，构造方式与dict相同

        """
        super(ConfigDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def copy(self):
        """ 返回一个参数字典的深拷贝

        Returns
        -------
        config_copy : ConfigDict
            参数字典的深拷贝
        """
        return ConfigDict(**self)


def _valid_qt_kwargs():
    """ 合法参数列表

    构建一个合法参数列表，用于控制qteasy的运行方式。合法参数列表是一个dict of dict，每一个key是一个合法的参数名，
    每一个value是一个dict，包含4个key，分别是"Default", "Validator", "level", "text"，对应的value分别是：
        "Default"      - 如果用户没有指定该参数，则使用该默认值
        "Validator"    - 一个函数，用于验证用户指定的参数值是否合法
        "level"        - 该参数的显示级别，用户可以选择显示不同级别的参数，以节省时间
        "text"         - 该参数的说明文本，用户可以通过显示该文本来了解该参数的含义

    Returns
    -------
    vkwargs : dict
        合法参数列表
    """
    vkwargs = {
        'mode':
            {'Default':   1,  # 运行模式
             'Validator': lambda value: value in (0, 1, 2, 3),
             'level':     0,
             'text':      'qteasy 的运行模式: \n'
                          '0: 实盘运行模式\n'
                          '1: 回测-评价模式\n'
                          '2: 策略优化模式\n'
                          '3: 统计预测模式\n'},

        'time_zone':  # this parameter is now not used
            {'Default':   'local',
             'Validator': lambda value: _validate_time_zone(value),
             'level':     4,
             'text':      '回测时的时区，默认值"local"，表示使用本地时区。\n'
                          '如果需要固定时区，设置任意合法的时区，例如：\n'
                          'Asia/Shanghai\n'
                          'Asia/Hong_Kong\n'
                          'US/Eastern\n'
                          'US/Pacific\n'
                          'Europe/London\n'
                          'Europe/Paris\n'
                          'Australia/Sydney\n'
                          'Australia/Melbourne\n'
                          'Pacific/Auckland\n'
                          'Pacific/Chatham\n'
                          'etc.\n'},

        'asset_pool':
            {'Default':   '000300.SH',  #
             'Validator': lambda value: isinstance(value, (str, list))
                                        and _validate_asset_pool(value),
             'level':     0,
             'text':      '可用投资产品池，投资组合基于池中的产品创建'},

        'asset_type':
            {'Default':   'IDX',  #
             'Validator': lambda value: isinstance(value, str)
                                        and _validate_asset_type(value),
             'level':     0,
             'text':      '投资产品的资产类型，包括：\n'
                          'IDX  : 指数\n'
                          'E    : 股票\n'
                          'FT   : 期货\n'
                          'FD   : 基金\n'},

        'live_trade_account_id':
            {'Default':   None,  # 指定account_id后，实盘交易时会直接使用该账户，除非账户不存在
             'Validator': lambda value: isinstance(value, int) or value is None,
             'level':     0,
             'text':      '实盘交易账户ID，用于实盘交易，如果指定了该参数，则会直接\n'
                          '使用该账户，除非账户不存在'},

        'live_trade_account':
            {'Default':   None,  # 指定account后，会查找该账户对应的account_id并使用该账户，除非账户不存在
             'Validator': lambda value: isinstance(value, str) or value is None,
             'level':     0,
             'text':      '实盘交易账户名称，用于实盘交易，如果指定了该参数，则会查找该\n'
                          '账户对应的account_id并使用该账户，除非账户不存在'},

        'live_trade_debug_mode':
            {'Default':   False,
             'Validator': lambda value: isinstance(value, bool),
             'level':     1,
             'text':      '实盘交易调试模式，True: 调试模式，False: 正常模式'},

        'live_trade_init_cash':
            {'Default':   1000000.0,
             'Validator': lambda value: isinstance(value, (int, float))
                                        and value > 0,
             'level':     1,
             'text':      '实盘交易账户的初始资金，浮点数，例如：\n'
                          '1000000.0 : 初始资金为100万\n'
                          '1000000   : 初始资金为100万\n'},

        'live_trade_init_holdings':
            {'Default':   None,
             'Validator': lambda value: isinstance(value, dict) or value is None,
             'level':     1,
             'text':      '实盘交易账户的初始持仓，字典，例如：\n'
                          "{'000001.SZ': 1000, '000002.SZ': 2000} : 初始持仓为\n"
                          "000001.SZ: 1000股, 000002.SZ: 2000股\n"},

        'live_trade_broker_type':
            {'Default':   'simulator',
             'Validator': lambda value: isinstance(value, str) and value.lower() in ['simulator',
                                                                                     'simple',
                                                                                     'random',  # to be deprecated
                                                                                     'manual',
                                                                                     ],
             'level':     1,
             'text':      '实盘交易账户的交易代理商类型，可以设置为模拟交易代理商返回交易结果、'
                          '手动输入结果或者连接到交易代理商的交易接口\n'
                          '默认使用模拟交易代理Simulator'},

        'live_trade_broker_params':
            {'Default':   None,
             'Validator': lambda value: isinstance(value, dict) or value is None,
             'level':     1,
             'text':      '实盘交易账户的交易代理商参数，字典，例如：\n'
                          "{'host': 'localhost', 'port': 8888} : 交易代理商的主机名和端口号\n"
                          "具体的参数设置请参考交易代理商的文档\n"
                          "如果使用 'simulator' broker，且设置此参数为None，则会使用config中的\n"
                          "backtest参数"},

        'live_price_acquire_channel':
            {'Default':   'eastmoney',
             'Validator': lambda value: isinstance(value, str) and value.lower() in ['eastmoney', 'tushare', 'akshare'],
             'level':     2,
             'text':      '实盘交易时获取实时价格的方式：\n'
                          'eastmoney - 通过东方财富网获取实时价格\n'
                          'tushare  - 通过tushare获取实时价格(需要自行开通权限)\n'
                          'akshare  - Not Implemented: 从akshare获取实时价格\n'},

        'live_price_acquire_freq':
            {'Default':   '15MIN',
             'Validator': lambda value: isinstance(value, str) and value.upper() in
                                        ['H', '30MIN', '15MIN', '5MIN', '1MIN', 'TICK'],
             'level':     2,
             'text':      '实盘交易时获取实时价格的频率：\n'
                          'H      - 每1小时获取一次数据\n'
                          '30MIN  - 每30分钟获取一次数据\n'
                          '15MIN  - 每15分钟获取一次数据\n'
                          '5MIN   - 每5分钟获取一次数据\n'
                          '1MIN   - 每1分钟获取一次数据\n'},

        'watched_price_refresh_interval':
            {'Default':   5,
             'Validator': lambda value: isinstance(value, int) and value >= 5,
             'level':     4,
             'text':      '实盘交易时监看实时价格的刷新频率，单位为秒，默认为5秒\n'
                          '该数值不能低于5秒'},

        'trade_batch_size':
            {'Default':   0.0,
             'Validator': lambda value: isinstance(value, (int, float))
                                        and value >= 0,
             'level':     0,
             'text':      '投资产品的最小申购批量大小，浮点数，例如：\n'
                          '0. : 可以购买任意份额的投资产品，包括小数份额\n'
                          '1. : 只能购买整数份额的投资产品\n'
                          '100: 可以购买100的整数倍份额投资产品\n'
                          'n  : 可以购买的投资产品份额为n的整数倍，n不必为整数\n'},

        'sell_batch_size':
            {'Default':   0.0,
             'Validator': lambda value: isinstance(value, (int, float))
                                        and value >= 0,
             'level':     0,
             'text':      '投资产品的最小卖出或赎回批量大小，浮点数，例如：\n'
                          '0. : 可以购买任意份额的投资产品，包括小数份额\n'
                          '1. : 只能购买整数份额的投资产品\n'
                          '100: 可以购买100的整数倍份额投资产品\n'
                          'n  : 可以购买的投资产品份额为n的整数倍，n不必为整数\n'},

        'cash_decimal_places':
            {'Default':   2,
             'Validator': lambda value: isinstance(value, int) and value >= 0,
             'level':     2,
             'text':      '现金的小数位数，例如：\n'
                          '0: 现金只能为整数\n'
                          '2: 保留小数点后两位数字\n'},

        'amount_decimal_places':
            {'Default':   2,
             'Validator': lambda value: isinstance(value, int) and value >= 0,
             'level':     2,
             'text':      '投资产品的份额的小数位数，例如：\n'
                          '0: 份额只能为整数\n'
                          '2: 保留小数点后两位数字\n'},

        'riskfree_ir':
            {'Default':   0.0035,
             'Validator': lambda value: isinstance(value, float)
                                        and 0 <= value < 1,
             'level':     1,
             'text':      '无风险利率，如果选择"考虑现金的时间价值"，则回测时现金按此年利率增值'},

        'parallel':
            {'Default':   True,
             'Validator': lambda value: isinstance(value, bool),
             'level':     1,
             'text':      '如果True，策略参数寻优时将利用多核心CPU进行并行计算提升效率'},

        'hist_dnld_parallel':
            {'Default':   16,
             'Validator': lambda value: isinstance(value, int) and value >= 0,
             'level':     4,
             'text':      '下载历史数据时启用的线程数量，为0或1时采用单线程下载，大于1时启用多线程'},

        'hist_dnld_delay':
            {'Default':   0.,
             'Validator': lambda value: isinstance(value, float) and value >= 0,
             'level':     4,
             'text':      '为防止服务器数据压力过大，下载历史数据时下载一定数量的数据后延迟的时间长度，单位为秒'},

        'hist_dnld_delay_evy':
            {'Default':   0,
             'Validator': lambda value: isinstance(value, int) and value >= 0,
             'level':     4,
             'text':      '为防止服务器数据压力过大，下载历史数据时，每下载一定数量的数据，就延迟一段时间。\n'
                          '此参数为两次延迟之间的数据下载量'},

        'hist_dnld_prog_bar':
            {'Default':   False,
             'Validator': lambda value: isinstance(value, bool),
             'level':     4,
             'text':      '下载历史数据时是否显示进度条'},

        'hist_dnld_retry_cnt':
            {'Default':   7,
             'Validator': lambda value: isinstance(value, int) and
                                        0 < value <= 10,
             'level':     4,
             'text':      '下载历史数据失败时的自动重试次数'},

        'hist_dnld_retry_wait':
            {'Default':   1.,
             'Validator': lambda value: isinstance(value, (int, float)) and
                                        0.1 <= value <= 5.0,
             'level':     4,
             'text':      '下载历史数据失败时的自动重试前的延迟时间，单位为秒'},

        'hist_dnld_backoff':
            {'Default':   2.,
             'Validator': lambda value: isinstance(value, (int, float)) and
                                        1.0 <= value <= 3.0,
             'level':     4,
             'text':      '下载历史数据失败时的自动重试的延迟时间倍增乘数\n'
                          '例如，设置hist_dnld_backoff = 2时，每次重试失败\n'
                          '后延迟时间会变为前一次的2倍'},

        'auto_dnld_hist_tables':
            {'Default':   [],
             'Validator': lambda value: isinstance(value, list) and
                                        all(isinstance(item, str) for item in value),
             'level':     4,
             'text':      '在实盘运行时自动下载的历史数据表名列表，例如：\n'
                          '["stock_daily", "index_weekly", "stock_monthly"]\n'
                          '如果列表为空，则不自动下载任何历史数据'},

        'gpu':
            {'Default':   False,
             'Validator': lambda value: isinstance(value, bool),
             'level':     4,
             'text':      '如果True，策略参数寻优时使用GPU加速计算\n'
                          '<本功能目前尚未实现! NotImplemented>'},

        'local_data_source':
            {'Default':   'file',
             'Validator': lambda value: isinstance(value, str) and value.lower() in ['file',
                                                                                     'database',
                                                                                     'db'],
             'level':     1,
             'text':      '确定本地历史数据存储方式：\n'
                          'file     - 历史数据以本地文件的形式存储，\n'
                          '           文件格式在"local_data_file_type"属性中指定，包括csv/hdf等多种选项\n'
                          'database - 历史数据存储在一个mysql数据库中\n'
                          '           选择此选项时，需要在配置文件中配置数据库的连接信息\n'
                          'db       - 等同于"database"'},

        'local_data_file_type':
            {'Default':   'csv',
             'Validator': lambda value: isinstance(value, str) and value.lower() in ['csv',
                                                                                     'hdf',
                                                                                     'feather',
                                                                                     'fth'],
             'level':     4,
             'text':      '确定本地历史数据文件的存储格式：\n'
                          'csv - 历史数据文件以csv形式存储，速度较慢但可以用Excel打开\n'
                          'hdf - 历史数据文件以hd5形式存储，数据存储和读取速度较快\n'
                          'feather/fth - 历史数据文件以feather格式存储，数据交换速度快但不适用长期存储'},

        'local_data_file_path':
            {'Default':   'data/',
             'Validator': lambda value: isinstance(value, str),
             'level':     4,
             'text':      '确定本地历史数据文件存储路径'},

        'local_db_host':
            {'Default':   'localhost',
             'Validator': lambda value: isinstance(value, str),
             'level':     4,
             'text':      '用于存储历史数据的数据库的主机名，该数据库应该为mysql数据库或MariaDB'},

        'local_db_port':
            {'Default':   3306,
             'Validator': lambda value: isinstance(value, int) and 1024 < value < 49151,
             'level':     4,
             'text':      '用于存储历史数据的数据库的端口号，默认值为mysql数据库的端口号3306'},

        'local_db_name':
            {'Default':   'qt_db',
             'Validator': lambda value: isinstance(value, str) and
                                        (len(value) <= 255) and
                                        (all(char not in value for
                                             char in '+-/?<>{}[]()|\\!@#$%^&*=~`')),
             'level':     4,
             'text':      '用于存储历史数据的数据库名，默认值为"qt_db"'},

        'local_db_user':
            {'Default':   '',
             'Validator': lambda value: isinstance(value, str),
             'level':     4,
             'text':      '访问数据库的用户名，该用户需具备足够的操作权限\n'
                          '建议通过配置文件配置数据库用户名和密码'},

        'local_db_password':
            {'Default':   '',
             'Validator': lambda value: isinstance(value, str),
             'level':     4,
             'text':      '数据库的访问密码\n\n'
                          '建议通过配置文件配置数据库用户名和密码'},

        'sys_log_file_path':
            {'Default':   'syslog/',
             'Validator': lambda value: isinstance(value, str),
             'level':     4,
             'text':      '系统运行日志及错误日志的存储路径\n'},

        'trade_log_file_path':
            {'Default':   'tradelog/',
             'Validator': lambda value: isinstance(value, str),
             'level':     4,
             'text':      '明细交易日志的存储路径\n'},

        'trade_log':
            {'Default':   True,
             'Validator': lambda value: isinstance(value, bool),
             'level':     1,
             'text':      '是否生成明细交易清单，以pd.DataFrame形式给出明细的每日交易清单\n'
                          '包括交易信号以及每一步骤的交易结果'},

        'benchmark_asset':
            {'Default':   '000300.SH',  # TODO: 未来版本支持多个基准
             'Validator': lambda value: isinstance(value, str)
                                        and _validate_asset_symbol(value),
             'level':     1,
             'text':      '用来产生回测结果评价结果基准收益的资产类型，默认基准为沪深300指数\n'
                          '基准指数用来生成多用评价结果如alpha、beta比率等，因为这些指标除了考察投资收益的\n'
                          '绝对值意外，还需要考虑同时期的市场平均表现，只有当投资收益优于市场平均表现的，才会\n'
                          '被算作超额收益或alpha收益，这才是投资策略追求的目标'},

        'benchmark_asset_type':
            {'Default':   'IDX',
             'Validator': lambda value: _validate_asset_type(value),
             'level':     1,
             'text':      '基准收益的资产类型，包括：\n'
                          'IDX  : 指数\n'
                          'E    : 股票\n'
                          'FT   : 期货\n'
                          'FD   : 基金\n'},

        'benchmark_dtype':
            {'Default':   'close',
             'Validator': lambda value: value.lower() in ['open',
                                                          'high',
                                                          'low',
                                                          'close',
                                                          'vol',
                                                          'unit_nav',
                                                          'accum_nav'],
             'level':     1,
             'text':      '作为基准收益的资产的价格类型。'},

        'report':
            {'Default':   True,
             'Validator': lambda value: isinstance(value, bool),
             'level':     1,
             'text':      '为True时打印运行结果报告\n'
                          '实时模式显示策略运行报告，'
                          '回测模式显示回测结果报告，'
                          '优化模式显示优化结果报告'},

        'visual':
            {'Default':   True,
             'Validator': lambda value: isinstance(value, bool),
             'level':     0,
             'text':      '为True时使用图表显示可视化运行结果\n'
                          '（回测模式显示回测报告，优化模式显示优化结果报告）'},

        'buy_sell_points':
            {'Default':   True,
             'Validator': lambda value: isinstance(value, bool),
             'level':     4,
             'text':      '为True时在回测图表中显示买卖点，使用红色和绿色箭头标示出买卖点的位置'},

        'show_positions':
            {'Default':   True,
             'Validator': lambda value: isinstance(value, bool),
             'level':     4,
             'text':      '为True时在回测图表中用色带显示投资仓位'},

        'cost_fixed_buy':
            {'Default':   0.,
             'Validator': lambda value: isinstance(value, float)
                                        and value >= 0,
             'level':     2,
             'text':      '买入证券或资产时的固定成本或固定佣金，该金额不随买入金额变化\n'
                          '默认值为10元'},

        'cost_fixed_sell':
            {'Default':   0.,
             'Validator': lambda value: isinstance(value, float)
                                        and value >= 0,
             'level':     2,
             'text':      '卖出证券或资产时的固定成本或固定佣金，该金额不随卖出金额变化\n'
                          '默认值为0'},

        'cost_rate_buy':
            {'Default':   0.0003,
             'Validator': lambda value: isinstance(value, float)
                                        and 0 <= value < 1,
             'level':     1,
             'text':      '买入证券或资产时的成本费率或佣金比率，以买入金额的比例计算\n'
                          '默认值为万分之三'},

        'cost_rate_sell':
            {'Default':   0.0001,
             'Validator': lambda value: isinstance(value, float)
                                        and 0 <= value < 1,
             'level':     1,
             'text':      '卖出证券或资产时的成本费率或佣金比率，以卖出金额的比例计算\n'
                          '默认值为万分之一'},

        'cost_min_buy':
            {'Default':   5.0,
             'Validator': lambda value: isinstance(value, float)
                                        and value >= 0,
             'level':     2,
             'text':      '买入证券或资产时的最低成本或佣金，买入佣金只能大于或等于该最低金额\n'
                          '默认值为5元'},

        'cost_min_sell':
            {'Default':   5.0,
             'Validator': lambda value: isinstance(value, float)
                                        and value >= 0,
             'level':     2,
             'text':      '卖出证券或资产时的最低成本或佣金，卖出佣金只能大于或等于该最低金额'},

        'cost_slippage':
            {'Default':   0.0,
             'Validator': lambda value: isinstance(value, float)
                                        and 0 <= value < 1,
             'level':     2,
             'text':      '交易滑点，一个预设参数，模拟由于交易延迟或交易金额过大产生的额外交易成本'},

        'invest_start':
            {'Default':   '20160405',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_datelike(value),
             'level':     0,
             'text':      '回测模式下的回测开始日期\n'
                          '格式为"YYYYMMDD"'},

        'invest_end':
            {'Default':   '20210201',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_datelike(value),
             'level':     0,
             'text':      '回测模式下的回测结束日期\n'
                          '格式为"YYYYMMDD"'},

        'invest_cash_amounts':
            {'Default':   [100000.0],
             'Validator': lambda value: isinstance(value, (tuple, list))
                                        and all(isinstance(item, (float, int))
                                                for item in value)
                                        and all(item > 1 for item in value),
             'level':     1,
             'text':      '投资的金额，一个tuple或list，每次投入资金的金额，多个数字表示多次投入'},

        'invest_cash_dates':
            {'Default':   None,
             'Validator': lambda value: isinstance(value, (str, list))
                                        and all(isinstance(item, str)
                                                for item in value) or value is None,
             'level':     2,
             'text':      '回测操作现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None\n'
                          '当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖\n'
                          'invest_start\n'
                          '参数输入类型为str时，格式为"YYYYMMDD"\n'
                          '如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型\n'
                          '以下两种输入方式等效：\n'
                          '"20100104,20100202,20100304" = \n'
                          '["20100104", "20100202", "20100304"]'},

        'allow_sell_short':
            {'Default':   False,
             'Validator': lambda value: isinstance(value, bool),
             'level':     4,
             'text':      '是否允许卖空交易，：\n'
                          '- False - 默认值，不允许卖空操作，卖出数量最多仅为当前可用持仓数量\n'
                          '- True -  允许卖空，卖出数量大于持仓量时，即持有空头仓位\n'},

        'long_position_limit':
            {'Default':   1.,
             'Validator': lambda value: isinstance(value, float) and (value > 0),
             'level':     3,
             'text':      '回测过程中允许交易信号建立的多头仓位百分比的极限值，即允许动用\n'
                          '总资产（包括现金和持有股票的总额）的多少百分比用于持有多头仓位，\n'
                          '默认值1.0，即100%\n'
                          '如果设置值大于1，则表示允许超过持有现金建仓，这种情况会产生负现金\n'
                          '余额，表示产生了借贷\n'},

        'short_position_limit':
            {'Default':   -1.,
             'Validator': lambda value: isinstance(value, float) and (value < 0),
             'level':     3,
             'text':      '回测过程中允许交易信号建立的空头仓位百分比的极限值，即允许持有的\n'
                          '空头仓位占当前净资产总额的最高比例限额，默认值-1.0，即最多允许借入\n'
                          '相当于净资产总额100%价值的股票并持有空头仓位，此时持有负股票份额且\n'
                          '产生正现金流入'},

        'backtest_price_adj':
            {'Default':   'none',
             'Validator': lambda value: isinstance(value, str)
                                        and value.lower() in ['none', 'n', 'back', 'b', 'adj'],
             'level':     4,
             'text':      '回测时的复权价格处理方法：\n'
                          '股票分红除权的处理，正常来说，应该在股票分红除权时计算分红和派息对持仓\n'
                          '数量和现金的影响，但是目前这种处理方法比较复杂，暂时先采用比较简单的方\n'
                          '法，即直接采用复权价格进行回测，目前处理方法有两种'
                          '- none/n - 默认值，不使用复权价格，但也不处理派息，这只是临时处理，因\n'
                          '           为长期回测不考虑除权派息将会导致回测结果与实际相差巨大\n'
                          '- back/b - 使用后复权价格回测，可以弥补不考虑分红派股的不足\n'
                          '- adj    - 使用前复权价格回测。\n'},

        'maximize_cash_usage':
            {'Default':   True,
             'Validator': lambda value: isinstance(value, bool),
             'level':     4,
             'text':      '回测交易时是否最大化利用同一批次交易获得的现金。即优先卖出股票并将获得的现金立即\n'
                          '用于同一批次的买入交易，以便最大限度利用可用现金。当现金的交割期大于0时无效。\n'
                          '- True -  默认值，首先处理同一批次交易中的卖出信号，并在可能时将获得的现金\n'
                          '          立即用于本次买入\n'
                          '- False - 同批次买入和卖出信号同时处理，不立即使用卖出资产的现金将同一批\n'
                          '          次交易委托同时提交时，这是正常情况'},

        'PT_signal_timing':
            {'Default':   'lazy',
             'Validator': lambda value: value.lower() in ['aggressive', 'lazy'],
             'level':     3,
             'text':      '回测信号模式为PT（position target）时，控制检查实际持仓比例并自动生成交易\n'
                          '信号的时机，默认normal\n'
                          '- aggressive: 在整个策略运行时间点上都会产生交易信号，不论此时PT信号是否发\n'
                          '              生变化，实时监控实际持仓与计划持仓之间的差异，只要二者发生偏\n'
                          '              离，就产生信号\n'
                          '- lazy:       在策略运行时间点上，只有当持仓比例发生变化时，才会产生交易\n'
                          '              信号，不实时监控实际持仓与计划持仓的差异'},

        'PT_buy_threshold':
            {'Default':   0.,
             'Validator': lambda value: isinstance(value, (float, int))
                                        and (0 <= value < 1),
             'level':     3,
             'text':      '回测信号模式为PT（position target）时，触发买入信号的仓位差异阈值\n'
                          '在这种模式下，当持有的投资产品的仓位比目标仓位低，且差额超过阈值时，触发买入信号\n'
                          '例如当卖出阈值为0.05即5%时，若目标持仓30%，那么只有当实际持仓<=25%时，才会产生\n'
                          '交易信号，即此时实际持仓与目标持仓之间的差值大于5%了'},

        'PT_sell_threshold':
            {'Default':   0.,
             'Validator': lambda value: isinstance(value, (float, int))
                                        and (0 <= value < 1),
             'level':     3,
             'text':      '回测信号模式为PT（position target）时，触发卖出信号的仓位差异阈值\n'
                          '在这种模式下，当持有的投资产品的仓位比目标仓位高，且差额超过阈值时，触发卖出信号\n'
                          '例如当卖出阈值为0.05即5%时，若目标持仓30%，那么只有当实际持仓>=35%时，才会产生\n'
                          '交易信号，即此时实际持仓与目标持仓之间的差值大于5%了'},

        'price_priority_OHLC':
            {'Default':   'OHLC',
             'Validator': lambda value: isinstance(value, str)
                                        and all(item.upper() in 'OHLCA'
                                                for item in value)
                                        and all(item.upper() in value
                                                for item in 'OHLC'),
             'level':     3,
             'text':      '回测时如果存在多种价格类型的交易信号，而且交易价格的类型为OHLC时，处理各种\n'
                          '不同的价格信号的优先级。\n'
                          '输入类型为字符串，O、H、L、C、A分别代表Open,High,Low,Close,Nav\n'},

        'price_priority_quote':
            {'Default':   'normal',
             'Validator': lambda value: isinstance(value, str)
                                        and (value in ['normal', 'reverse']),
             'level':     3,
             'text':      '回测时如果存在多种价格类型的交易信号，而且交易价格的类型为实时报价时，回测程序处理\n'
                          '不同的价格信号的优先级。\n'
                          '输入包括"normal" 以及 "reverse"两种，分别表示：\n'
                          '- "normal"：  优先处理更接近成交价的报价，如卖1/买1等\n'
                          '- "reverse"： 优先处理更远离成交价的报价，如卖5/买5等'},

        'cash_delivery_period':
            {'Default':   0,
             'Validator': lambda value: isinstance(value, int)
                                        and value in range(5),
             'level':     3,
             'text':      '回测时卖出股票获得现金的交割周期，用一个数字N代表交易日后第N天可以完成现金交割。\n'
                          '获得现金后立即计入总资产，但在途资金（尚未交割的资金）不能用于下一笔交易\n'
                          '当现金交割期为零时，可以选择在同一轮交易中先卖出资产获得尽可能多的现金用于本轮\n'
                          '买入'},

        'stock_delivery_period':
            {'Default':   1,
             'Validator': lambda value: isinstance(value, int)
                                        and value in range(5),
             'level':     3,
             'text':      '回测时买入股票后的股票交割周期，用一个数字N代表交易日后第N天可以完成资产交割。\n'
                          '获得股票后立即计入总资产，但尚未交割的股票不能用于下一笔交易'},

        'market_open_time_am':
            {'Default':   '09:30:00',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_timelike(value),
             'level':     3,
             'text':      '交易市场上午开市时间'},

        'market_close_time_am':
            {'Default':   '11:30:00',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_timelike(value),
             'level':     3,
             'text':      '交易市场上午收市时间'},

        'market_open_time_pm':
            {'Default':   '13:00:00',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_timelike(value),
             'level':     3,
             'text':      '交易市场下午开市时间'},

        'market_close_time_pm':
            {'Default':   '15:00:00',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_timelike(value),
             'level':     3,
             'text':      '交易市场下午收市时间'},

        'strategy_open_close_timing_offset':
            {'Default':   1,
             'Validator': lambda value: isinstance(value, int)
                                        and value in range(5),
             'level':     3,
             'text':      '策略信号的开盘/收盘运行时间偏移量，单位为分钟，当策略信号运行时机为开盘/收盘，需要提前/推迟\n'
                          '一个偏移量运行，避免无法交易。'},

        'opti_start':
            {'Default':   '20160405',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_datelike(value),
             'level':     0,
             'text':      '优化模式下的策略优化区间开始日期'},

        'opti_end':
            {'Default':   '20191231',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_datelike(value),
             'level':     0,
             'text':      '优化模式下的策略优化区间结束日期'},

        'opti_cash_amounts':
            {'Default':   [100000.0],
             'Validator': lambda value: isinstance(value, (tuple, list))
                                        and all(isinstance(item, (float, int))
                                                for item in value)
                                        and all(item > 1 for item in value),
             'level':     1,
             'text':      '优化模式投资的金额，一个tuple或list，每次投入资金的金额，多个数字表示多次投入'},

        'opti_cash_dates':
            {'Default':   None,
             'Validator': lambda value: isinstance(value, (str, list))
                                        and all(isinstance(item, str)
                                                for item in value) or value is None,
             'level':     2,
             'text':      '策略优化区间现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None\n'
                          '当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖\n'
                          'invest_start\n'
                          '参数输入类型为str时，格式为"YYYYMMDD"\n'
                          '如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型\n'
                          '以下两种输入方式等效：\n'
                          '"20100104,20100202,20100304"'
                          '["20100104", "20100202", "20100304"]'},

        'opti_type':
            {'Default':   'single',
             'Validator': lambda value: isinstance(value, str) and value in ['single', 'multiple'],
             'level':     3,
             'text':      '优化类型。指优化数据的利用方式:\n'
                          '"single"   - 在每一回合的优化测试中，在优化区间上进行覆盖整个区间的单次回测并评价\n'
                          '             回测结果\n'
                          '"multiple" - 在每一回合的优化测试中，将优化区间的数据划分为多个子区间，在这些子\n'
                          '             区间上分别测试，并根据所有测试的结果确定策略在整个区间上的评价结果'},

        'opti_sub_periods':
            {'Default':   5,
             'Validator': lambda value: isinstance(value, int) and value >= 1,
             'level':     3,
             'text':      '仅对无监督优化有效。且仅当优化类型为"multiple"时有效。将优化区间切分为子区间的数量'},

        'opti_sub_prd_length':
            {'Default':   0.6,
             'Validator': lambda value: isinstance(value, float) and 0 <= value <= 1.,
             'level':     3,
             'text':      '仅当优化类型为"multiple"时有效。每一个优化子区间长度占整个优化区间长度的比例\n'
                          '例如，当优化区间长度为10年时，本参数为0.6代表每一个优化子区间长度为6年'},

        'test_start':
            {'Default':   '20200106',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_datelike(value),
             'level':     0,
             'text':      '优化模式下的策略测试区间开始日期'
                          '格式为"YYYYMMDD"'
                          '字符串类型输入'},

        'test_end':
            {'Default':   '20210201',
             'Validator': lambda value: isinstance(value, str)
                                        and _is_datelike(value),
             'level':     0,
             'text':      '优化模式下的策略测试区间结束日期\n'
                          '格式为"YYYYMMDD"'
                          '字符串类型输入'},

        'test_cash_amounts':
            {'Default':   [100000.0],
             'Validator': lambda value: isinstance(value, (tuple, list))
                                        and all(isinstance(item, (float, int))
                                                for item in value)
                                        and all(item > 1 for item in value),
             'level':     1,
             'text':      '优化模式策略测试投资的金额，一个tuple或list，每次投入资金的金额。\n'
                          '模拟现金多次定投投入时，输入多个数字表示多次投入\n'
                          '输入的数字的个数必须与cash_dates中的日期数量相同'},

        'test_cash_dates':
            {'Default':   None,
             'Validator': lambda value: isinstance(value, (str, list))
                                        and all(isinstance(item, str)
                                                for item in value) or value is None,
             'level':     2,
             'text':      '策略优化区间现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None\n'
                          '当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖\n'
                          'invest_start参数\n'
                          '参数输入类型为str时，格式为"YYYYMMDD"\n'
                          '如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型\n'
                          '以下两种输入方式等效：\n'
                          '"20100104,20100202,20100304"'
                          '["20100104", "20100202", "20100304"]'},

        'test_type':
            {'Default':   'single',
             'Validator': lambda value: isinstance(value, str) and
                                        value in ['single', 'multiple', 'montecarlo'],
             'level':     3,
             'text':      '测试类型。指测试数据的利用方式:\n'
                          '"single"     - 在每一回合的优化测试中，在测试区间上进行覆盖整个区间的单次回测\n'
                          '               并评价回测结果\n'
                          '"multiple"   - 在每一回合的优化测试中，将测试区间的数据划分为多个子区间，在这\n'
                          '               些子区间上分别测试，并根据所有测试的结果确定策略在整个区间上的\n'
                          '               评价结果\n'
                          '"montecarlo" - 蒙特卡洛测试，根据测试区间历史数据的统计性质，随机生成大量的模\n'
                          '               拟价格变化数据，用这些数据对策略的表现进行评价，最后给出统计意\n'
                          '               义的评价结果'},

        'test_indicators':
            {'Default':   'years,fv,return,mdd,v,ref,alpha,beta,sharp,info',
             'Validator': lambda value: isinstance(value, str),
             'level':     2,
             'text':      '对优化后的策略参数进行测试评价的评价指标。\n'
                          '格式为逗号分隔的字符串，多个评价指标会以字典的形式输出，包含以下类型中的一种或多种\n'
                          '"years"       - total year\n'
                          '"fv"          - final values\n'
                          '"return"      - total return rate\n'
                          '"mdd"         - max draw down\n'
                          '"ref"         - reference data return\n'
                          '"alpha"       - alpha rate\n'
                          '"beta"        - beta rate\n'
                          '"sharp"       - sharp rate\n'
                          '"info"        - info rate'},

        'indicator_plot_type':
            {'Default':   'histo',
             'Validator': lambda value: _validate_indicator_plot_type(value),
             'level':     2,
             'text':      '优化或测试结果评价指标的可视化图表类型:\n'
                          '0  - errorbar 类型\n'
                          '1  - scatter 类型\n'
                          '2  - histo 类型\n'
                          '3  - violin 类型\n'
                          '4  - box 类型'},

        'test_sub_periods':
            {'Default':   3,
             'Validator': lambda value: isinstance(value, int) and value >= 1,
             'level':     3,
             'text':      '仅当测试类型为"multiple"时有效。将测试区间切分为子区间的数量'},

        'test_sub_prd_length':
            {'Default':   0.75,
             'Validator': lambda value: isinstance(value, float) and 0 <= value <= 1.,
             'level':     3,
             'text':      '仅当测试类型为"multiple"时有效。每一个测试子区间长度占整个测试区间长度的比例\n'
                          '例如，当测试区间长度为4年时，本参数0.75代表每个测试子区间长度为3年'},

        'test_cycle_count':
            {'Default':   100,
             'Validator': lambda value: isinstance(value, int) and value >= 1,
             'level':     3,
             'text':      '仅当测试类型为"montecarlo"时有效。生成的模拟测试数据的数量。\n'
                          '默认情况下生成100组模拟价格数据，并进行100次策略回测并评价其统计结果'},

        'optimize_target':
            {'Default':   'final_value',
             'Validator': lambda value: isinstance(value, str)
                                        and value in ['final_value', 'FV', 'SHARP'],
             'level':     1,
             'text':      '策略的优化目标。即优化时以找到该指标最佳的策略为目标'},

        'maximize_target':
            {'Default':   True,
             'Validator': lambda value: isinstance(value, bool),
             'level':     1,
             'text':      '为True时寻找目标值最大的策略，为False时寻找目标值最低的策略'},

        'opti_method':
            {'Default':   1,
             'Validator': lambda value: isinstance(value, int)
                                        and value <= 3,
             'level':     1,
             'text':      '策略优化算法，可选值如下:\n'
                          '0 - 网格法，按照一定间隔对整个向量空间进行网格搜索\n'
                          '1 - 蒙特卡洛法，在向量空间中随机取出一定的点搜索最佳策略\n'
                          '2 - 递进步长法，对向量空间进行多轮搜索，每一轮搜索结束后根据结果选择部分子\n'
                          '    空间，缩小步长进一步搜索\n'
                          '3 - 遗传算法，模拟生物种群在环境压力下不断进化的方法寻找全局最优（尚未完成）\n'
                          '4 - ML方法，基于机器学习的最佳策略搜索算法（尚未完成）\n'},

        'opti_grid_size':
            {'Default':   1,
             'Validator': lambda value: _num_or_seq_of_num(value) and value > 0,
             'level':     3,
             'text':      '使用穷举法搜索最佳策略时有用，搜索步长'},

        'opti_sample_count':
            {'Default':   256,
             'Validator': lambda value: isinstance(value, int) and value > 0,
             'level':     3,
             'text':      '使用蒙特卡洛法搜索最佳策略时有用，在向量空间中采样的数量'},

        'opti_r_sample_count':
            {'Default':   16,
             'Validator': lambda value: _num_or_seq_of_num(value)
                                        and value >= 0,
             'level':     3,
             'text':      '在使用递进步长法搜索最佳策略时有用，每一轮随机取样的数量'},

        'opti_reduce_ratio':
            {'Default':   0.1,
             'Validator': lambda value: isinstance(value, float)
                                        and 0 < value < 1,
             'level':     3,
             'text':      '在使用递进步长法搜索最佳策略时有用，\n'
                          '每一轮随机取样后择优留用的比例，同样也是子空间缩小的比例\n'},

        'opti_max_rounds':
            {'Default':   5,
             'Validator': lambda value: isinstance(value, int)
                                        and value > 1,
             'level':     3,
             'text':      '在使用递进步长法搜索最佳策略时有用，多轮搜索的最大轮数，轮数大于该值时停止搜索'},

        'opti_min_volume':
            {'Default':   1000,
             'Validator': lambda value: isinstance(value, (float, int))
                                        and value > 0,
             'level':     3,
             'text':      '在使用递进步长法搜索最佳策略时有用，空间最小体积，当空间volume低于该值时停止搜索'},

        'opti_population':
            {'Default':   1000.0,
             'Validator': lambda value: isinstance(value, float)
                                        and value >= 0,
             'level':     3,
             'text':      '在使用遗传算法搜索最佳策略时有用，种群的数量'},

        'opti_output_count':
            {'Default':   30,
             'Validator': lambda value: isinstance(value, int)
                                        and value > 0,
             'level':     3,
             'text':      '策略参数优化后输出的最优参数数量'},

    }
    _validate_vkwargs_dict(vkwargs)

    return vkwargs


def _validate_vkwargs_dict(vkwargs):
    """ 检查确认vkwargs合法参数列表的格式是否正确

    Parameters
    ----------
    vkwargs: dict
        合法参数列表

    Returns
    -------
    """
    for key, value in vkwargs.items():
        if len(value) != 4:
            raise ValueError(f'Items != 2 in valid config_key table, for config_key {key}')
        if 'Default' not in value:
            raise ValueError(f'Missing "Default" value for config_key {key}')
        if 'Validator' not in value:
            raise ValueError(f'Missing "Validator" function for config_key {key}')
        if 'level' not in value:
            raise ValueError(f'Missing "level" identifier for config_key {key}')
        if 'text' not in value:
            raise ValueError(f'Missing "text" string for config_key {key}')


def _vkwargs_to_text(kwargs, level=0, info=False, verbose=False, width=80):
    """ 给出一个或多个参数名称, 确认他们是否合法参数名称，并显示它们的当前值和其他信息
    返回一个字符串，包含所有参数的信息

    Parameters
    ----------
    kwargs: dict,
        需要显示的kwargs
    level: int or list of ints,
        所有需要输出的kwargs的层级
    info: bool
        是否输出基本信息
    verbose: bool
        是否输出详细信息
    width: int
        输出结果每一行占用的字符数

    Returns
    -------
    output_strings: str
        包含所有参数信息的字符串
    """
    from qteasy.utilfuncs import reindent, adjust_string_length
    if isinstance(level, int):
        levels = [level]
    elif isinstance(level, list):
        levels = level
    elif level == 'all':
        levels = [0, 1, 2, 3, 4]
    else:
        raise TypeError(f'level should be an integer or list of integers, got {type(level)}')
    assert all(isinstance(item, int) for item in levels), f'TypeError, levels should be a list of integers'
    column_w_key = min(int(width * 0.2), 30)
    column_w_default = min(int(width * 0.2), 30)
    column_w_current = width - column_w_key - column_w_default - 4
    column_offset_description = 4
    vkwargs = _valid_qt_kwargs()
    output_strings = list()
    if info:
        output_strings.append(f'No. {"Config - Key":<{column_w_key}}{"Cur Val":<{column_w_current}}'
                              f'{"Default val":<{column_w_default}}\n')
        if verbose:
            output_strings.append('      Description\n')
        output_strings.append(f'{"=" * width}\n')
    else:
        output_strings.append(f'No. {"Config - Key":<{column_w_key}}{"Cur Val":<{column_w_current}}\n')
        output_strings.append(f'{"=" * (width - column_w_default)}\n')
    no = 0
    for key in kwargs:
        if key not in vkwargs:
            from qteasy import logger_core
            logger_core.warning(f'Unrecognized config_key: <{str(key)}>')
            cur_value = str(kwargs[key])
            default_value = 'N/A'
            description = 'User-defined configuration key'
        else:
            cur_level = vkwargs[key]['level']
            if cur_level in levels:  # only display kwargs that are in the list of levels
                cur_value = str(kwargs[key])
                default_value = str(vkwargs[key]['Default'])
                description = str(vkwargs[key]['text'])
            else:
                continue

        no += 1
        output_strings.append(f'{no: <4}')
        output_strings.append(f'{adjust_string_length(str(key), column_w_key-1): <{column_w_key}}')
        if info:
            output_strings.append(
                    f'{adjust_string_length(cur_value, column_w_current-1): <{column_w_current}}'
                    f'<{adjust_string_length(default_value, column_w_default-3, padder="")}>\n')
            if verbose:
                output_strings.append(
                        f'{reindent(description, column_offset_description): <{column_w_key + column_w_current * 2}}'
                        f'\n\n'
                )
        else:
            output_strings.append(f'{cur_value}\n')
    return ''.join(output_strings)


def _initialize_config_kwargs(kwargs, vkwargs):
    """ Given a "valid kwargs table" and some kwargs, verify that each key-word
        is valid per the kwargs table, and that the value of the config_key is the
        correct type.  Fill a configuration dictionary with the default value
        for each config_key, and then substitute in any values that were provided
        as kwargs and return the configuration dictionary.

    Parameters
    ----------
    kwargs: keywords that is given by user
    vkwargs: valid keywords table usd for validating given kwargs

    Returns
    -------
        config_key: ConfigDict
    """
    # initialize configuration from valid_kwargs_table:
    config = ConfigDict()
    for key, value in vkwargs.items():
        config[key] = value['Default']

    # now validate kwargs, and for any valid kwargs
    #  replace the appropriate value in config_key:
    config = _update_config_kwargs(config, kwargs)

    return config


def _update_config_kwargs(config, kwargs, raise_if_key_not_existed=False):
    """ given existing configuration dict, verify that all kwargs are valid
        per kwargs table, and update the configuration dictionary

    Parameters
    ----------
    config: configuration dictionary to be updated
    kwargs: kwargs that are to be updated
    raise_if_key_not_existed:  if True, raise when key does not exist in vkwargs

    Returns
    -------
        config_key ConfigDict
    """
    vkwargs = _valid_qt_kwargs()
    for key in kwargs.keys():
        value = _parse_string_kwargs(kwargs[key], key, vkwargs)
        if _validate_key_and_value(key, value, raise_if_key_not_existed):
            config[key] = value

    return config


def _parse_string_kwargs(value, key, vkwargs):
    """ 如果value是字符串，将其转换为正确的参数类型

    从text文件中读取的参数都是字符串，需要将其转换为正确的参数类型

    Parameters
    ----------
    value: str
        需要转换的字符串，参数的值
    key: str
        参数名称
    vkwargs: dict
        有效参数表

    Returns
    -------
    value: any
        转换后的参数值
    """
    # 为防止value的类型不正确，将value修改为正确的类型，与 vkwargs 的
    # Default value 的类型相同
    if key not in vkwargs:
        return value
    if not isinstance(value, str):
        return value
    default_value = vkwargs[key]['Default']
    if (not isinstance(default_value, str)) and (default_value is not None):
        try:
            if isinstance(default_value, int):
                value = int(value)
            elif isinstance(default_value, float):
                value = float(value)
            elif isinstance(default_value, bool):
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                else:
                    raise TypeError(f'Invalid value: ({str(value)}) can not be converted to a boolean value')
            elif isinstance(default_value, (tuple, list)):
                default_list_value = default_value[0]
                values = value.strip('[](){}').split(',')
                if isinstance(default_list_value, int):
                    value = [int(item) for item in values]
                elif isinstance(default_list_value, float):
                    value = [float(item) for item in values]
                elif isinstance(default_list_value, str):
                    value = [str(item) for item in values]
                else:
                    raise TypeError(f'Invalid value: ({str(value)}) can not be converted to a list or tuple')

        except Exception as e:
            raise TypeError(f'({str(value)}) can not be converted to a valid value for config_key: <{key}>.\n'
                            f'Extra information: \n{vkwargs[key]["text"]}\n    {e}')
    return value


def _process_deprecated_keys(key):
    """ 如果key是deprecated的，触发将其转换为新的key

    Parameters
    ----------
    key : str
        需要检查的key

    Returns
    -------
    key: str 如果key是deprecated的，返回新的key，否则返回原key
    """

    deprecated = {
        'print_trade_log':    'trade_log',
        'print_backtest_log': 'trade_log',
    }

    # 处理 deprecated keys, send deprecation warning and use new key
    new_key = deprecated.get(key, key)
    if new_key != key:
        warnings.warn(f'config_key <{key}> is deprecated, please use <{new_key}> instead')
    return key


def _validate_key_and_value(key, value, raise_if_key_not_existed=False):
    """ 给定一个参数, 根据参数的验证方法验证值的正确性

    验证通过返回True, 否则返回报错
    如果参数不存在，则根据参数"raise_if_key_not_existed"的值决定报错或返回False

    Parameters
    ----------
    key: str
        需要验证的参数
    value: any
        被验证的参数值
    raise_if_key_not_existed: bool, default False
        当此参数为False时，如果key不存在，不会报错，而是返回False
        当此参数为True时，如果key不存在，会报错

    Returns
    -------
    bool : True or False
        如果验证通过，返回True
        如果参数不存在，且raise_if_key_not_existed为False，返回False

    Raises
    ------
    KeyError: 当key不存在且raise_if_key_not_existed为True时，会报错，否则返回False
    """
    vkwargs = _valid_qt_kwargs()

    if (key not in vkwargs) and raise_if_key_not_existed:
        err_msg = f'config_key: <{key}> is not a built-in parameter key, please check your input!'
        raise KeyError(err_msg)
    if key not in vkwargs:
        return True

    try:
        valid = vkwargs[key]['Validator'](value)
    except Exception as ex:
        ex.extra_info = f'Invalid value: ({str(value)}) for config_key: <{key}>.'
        raise ex
    if not valid:
        import inspect
        v = inspect.getsource(vkwargs[key]['Validator']).strip()
        raise TypeError(
                f'Invalid value: "{str(value)}"({type(value)}) for config_key: <{key}>\n'
                f'Extra information: \n{vkwargs[key]["text"]}\n    ' + v
        )

    return True


def _validate_asset_symbol(value):
    """ 检查确认value是一个合法的股票代码

    Parameters
    ----------
    value:

    Returns
    -------
    """
    if not isinstance(value, str):
        return False
    value = value.upper()
    from qteasy.utilfuncs import TS_CODE_IDENTIFIER_ALL
    import re
    if re.match(TS_CODE_IDENTIFIER_ALL, value) is None:
        return False

    return True


def _validate_indicator_plot_type(value):
    """ validate the value of indicator plot types, which include:

    '优化或测试结果评价指标的可视化图表类型:\n'
         '0  - errorbar 类型\n'
         '1  - scatter 类型\n'
         '2  - histo 类型\n'
         '3  - violin 类型\n'
         '4  - box 类型'

    Parameters:
    ----------
    value: int or str

    Returns:
    -------
    Boolean
    """
    if not isinstance(value, (int, str)):
        return False
    if isinstance(value, int):
        if not (0 <= value <= 4):
            return False
    else:
        if value not in ['errorbar',
                         'scatter',
                         'histo',
                         'violin',
                         'box']:
            return False
    return True


def _validate_asset_type(value: str):
    """

    Parameters
    ----------
    value:

    Returns
    -------
    bool
    """
    from .utilfuncs import AVAILABLE_ASSET_TYPES
    return value.upper() in AVAILABLE_ASSET_TYPES


def _validate_time_zone(value: str):
    """ 验证一个时区字符串的合法性

    Parameters
    ----------
    value: str

    Returns
    -------
    bool
    """
    if not isinstance(value, str):
        return False
    if value == 'local':
        return True
    from pytz import all_timezones_set
    return value in all_timezones_set


def _validate_asset_pool(value):
    """ 校验asset_pool的合法性，asset_pool中每一个元素都必须是一个合法的股票代码

    Parameters
    ----------
    value:

    Returns
    -------
    """
    if isinstance(value, str):
        from qteasy.utilfuncs import str_to_list
        value = str_to_list(value)
    if not isinstance(value, list):
        return False
    if any(not _validate_asset_symbol(v) for v in value):
        return False

    return True


def _is_datelike(value):
    """ return True if value is a date-like object
    """
    if isinstance(value, (pd.Timestamp, datetime.datetime, datetime.date)):
        return True
    if isinstance(value, str):
        try:
            dt = pd.to_datetime(value)
            return True
        except:
            return False
    return False


def _is_timelike(value):
    """ return True if value is a time-like object
    """
    if isinstance(value, (pd.Timestamp, datetime.datetime, datetime.time)):
        return True
    if isinstance(value, str):
        try:
            dt = pd.to_datetime(value)
            return True
        except:
            return False
    return False


def _num_or_seq_of_num(value):
    return (isinstance(value, (int, float)) or
            (isinstance(value, (list, tuple, np.ndarray)) and
             all([isinstance(v, (int, float)) for v in value]))
            )


def _bypass_kwarg_validation(value):
    """ For some kwargs, we either don't know enough, or
        the validation is too complex to make it worthwhile,
        so we bypass config_key validation.  If the config_key is
        invalid, then eventually an exception will be
        raised at the time the config_key value is actually used.
    """
    return True


def _kwarg_not_implemented(value):
    """ If you want to list a config_key in a valid_kwargs dict for a given
        function, but you have not yet, or don't yet want to, implement
        the config_key; or you simply want to (temporarily) disable the config_key,
        then use this function as the config_key validator
    """
    raise NotImplementedError('config_key NOT implemented.')


QT_CONFIG = _initialize_config_kwargs({}, _valid_qt_kwargs())