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
    """ 继承自dict的一个类，用于构造qt.run()函数的参数表字典对象
        比dict多出一个功能，即通过属性来访问字典的键值，提供访问便利性

        即：
        config_key.attr = config_key['attr']
    """

    def __init__(self, *args, **kwargs):
        """

        :rtype: object
        """
        super(ConfigDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def copy(self):
        """

        :return:
        """
        return ConfigDict(**self)


def _valid_qt_kwargs():
    """
    Construct and return the "valid kwargs table" for the qteasy.run() function.
    A valid kwargs table is a `dict` of `dict`s.  The keys of the outer dict are the
    valid key-words for the function.  The value for each key is a dict containing
    4 specific keys: "Default", "Validator", "level", and "text" with the following values:
        "Default"      - The default value for the config_key if none is specified.
        "Validator"    - A function that takes the caller specified value for the config_key,
                         and validates that it is the correct type, and (for kwargs with
                         a limited set of allowed values) may also validate that the
                         config_key value is one of the allowed values.
        "level"        - The display level of the key-word, for the user can choose to
                         display different levels of key-words at a time to save time
        "text"         - The explanatory text of the key-words, can be displayed for
                         easy access

    :return:
    """
    vkwargs = {
        'mode':                 {'Default':   1,  # 运行模式
                                 'Validator': lambda value: value in (0, 1, 2, 3),
                                 'level':     0,
                                 'text':      'qteasy 的运行模式: \n'
                                              '0: 实时信号生成模式\n'
                                              '1: 回测-评价模式\n'
                                              '2: 策略优化模式\n'
                                              '3: 统计预测模式\n'},

        'asset_pool':           {'Default':   '000300.SH',  #
                                 'Validator': lambda value: isinstance(value, (str, list))
                                                            and _validate_asset_pool(value),
                                 'level':     0,
                                 'text':      '可用投资产品池，投资组合基于池中的产品创建'},

        'asset_type':           {'Default':   'IDX',  #
                                 'Validator': lambda value: isinstance(value, str)
                                                            and _validate_asset_type(value),
                                 'level':     0,
                                 'text':      '投资产品的资产类型，包括：\n'
                                              'IDX  : 指数\n'
                                              'E    : 股票\n'
                                              'FT   : 期货\n'
                                              'FD   : 基金\n'},

        'trade_batch_size':     {'Default':   0.0,
                                 'Validator': lambda value: isinstance(value, (int, float))
                                                            and value >= 0,
                                 'level':     1,
                                 'text':      '投资产品的最小申购批量大小，浮点数，例如：\n'
                                              '0. : 可以购买任意份额的投资产品，包括小数份额\n'
                                              '1. : 只能购买整数份额的投资产品\n'
                                              '100: 可以购买100的整数倍份额投资产品\n'
                                              'n  : 可以购买的投资产品份额为n的整数倍，n不必为整数\n'},

        'sell_batch_size':      {'Default':   0.0,
                                 'Validator': lambda value: isinstance(value, (int, float))
                                                            and value >= 0,
                                 'level':     1,
                                 'text':      '投资产品的最小卖出或赎回批量大小，浮点数，例如：\n'
                                              '0. : 可以购买任意份额的投资产品，包括小数份额\n'
                                              '1. : 只能购买整数份额的投资产品\n'
                                              '100: 可以购买100的整数倍份额投资产品\n'
                                              'n  : 可以购买的投资产品份额为n的整数倍，n不必为整数\n'},

        'riskfree_ir':          {'Default':   0.0035,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and 0 <= value < 1,
                                 'level':     2,
                                 'text':      '无风险利率，如果选择"考虑现金的时间价值"，则回测时现金按此年利率增值'},

        'parallel':             {'Default':   True,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     1,
                                 'text':      '如果True，策略参数寻优时将利用多核心CPU进行并行计算提升效率'},

        'hist_dnld_parallel':   {'Default':   16,
                                 'Validator': lambda value: isinstance(value, int) and value >= 0,
                                 'level':     4,
                                 'text':      '下载历史数据时启用的线程数量，为0或1时采用单线程下载，大于1时启用多线程'},

        'hist_dnld_delay':      {'Default':   0.,
                                 'Validator': lambda value: isinstance(value, float) and value >= 0,
                                 'level':     4,
                                 'text':      '为防止服务器数据压力过大，下载历史数据时下载一定数量的数据后延迟的时间长度，单位为秒'},

        'hist_dnld_delay_evy':  {'Default':   0,
                                 'Validator': lambda value: isinstance(value, int) and value >= 0,
                                 'level':     4,
                                 'text':      '为防止服务器数据压力过大，下载历史数据时，每下载一定数量的数据，就延迟一段时间。\n'
                                              '此参数为两次延迟之间的数据下载量'},

        'hist_dnld_prog_bar':   {'Default':   False,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     4,
                                 'text':      '下载历史数据时是否显示进度条'},

        'hist_dnld_retry_cnt':  {'Default':   7,
                                 'Validator': lambda value: isinstance(value, int) and
                                                            0 < value <= 10,
                                 'level':     4,
                                 'text':      '下载历史数据失败时的自动重试次数'},

        'hist_dnld_retry_delay':
                                {'Default':   1.,
                                 'Validator': lambda value: isinstance(value, float) and
                                                            0. <= value <= 5.0,
                                 'level':     4,
                                 'text':      '下载历史数据失败时的自动重试前的延迟时间，单位为秒'},

        'hist_dnld_backoff':    {'Default':   2.,
                                 'Validator': lambda value: isinstance(value, float) and
                                                            0. <= value <= 2.0,
                                 'level':     4,
                                 'text':      '下载历史数据失败时的自动重试的延迟时间倍增乘数\n'
                                              '例如，设置hist_dnld_backoff = 2时，每次重试失败\n'
                                              '后延迟时间会变为前一次的2倍'},

        'gpu':                  {'Default':   False,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     4,
                                 'text':      '如果True，策略参数寻优时使用GPU加速计算\n'
                                              '<本功能目前尚未实现! NotImplemented>'},

        'local_data_source':    {'Default':   'file',
                                 'Validator': lambda value: isinstance(value, str) and value in ['file',
                                                                                                 'database',
                                                                                                 'db'],
                                 'level':     4,
                                 'text':      '确定本地历史数据存储方式：\n'
                                              'file     - 历史数据以本地文件的形式存储，\n'
                                              '           文件格式在"local_data_file_type"属性中指定，包括csv/hdf等多种选项\n'
                                              'database - 历史数据存储在一个mysql数据库中\n'
                                              '           选择此选项时，需要在配置文件中配置数据库的连接信息\n'
                                              'db       - 等同于"database"'},

        'local_data_file_type': {'Default':   'csv',
                                 'Validator': lambda value: isinstance(value, str) and value in ['csv',
                                                                                                 'hdf',
                                                                                                 'feather',
                                                                                                 'fth'],
                                 'level':     4,
                                 'text':      '确定本地历史数据文件的存储格式：\n'
                                              'csv - 历史数据文件以csv形式存储，速度较慢但可以用Excel打开\n'
                                              'hdf - 历史数据文件以hd5形式存储，数据存储和读取速度较快\n'
                                              'feather/fth - 历史数据文件以feather格式存储，数据交换速度快但不适用长期存储'},

        'local_data_file_path': {'Default':   'data/',
                                 'Validator': lambda value: isinstance(value, str),
                                 'level':     4,
                                 'text':      '确定本地历史数据文件存储路径'},

        'local_db_host':        {'Default':   'localhost',
                                 'Validator': lambda value: isinstance(value, str),
                                 'level':     4,
                                 'text':      '用于存储历史数据的数据库的主机名，该数据库应该为mysql数据库或MariaDB'},

        'local_db_port':        {'Default':   3306,
                                 'Validator': lambda value: isinstance(value, int) and 1024 < value < 49151,
                                 'level':     4,
                                 'text':      '用于存储历史数据的数据库的端口号，默认值为mysql数据库的端口号3306'},

        'local_db_name':        {'Default':   'qt_db',
                                 'Validator': lambda value: isinstance(value, str) and
                                                            (len(value) <= 255) and
                                                            (all(char not in value for
                                                                 char in '+-/?<>{}[]()|\\!@#$%^&*=~`')),
                                 'level':     4,
                                 'text':      '用于存储历史数据的数据库名，默认值为"qt_db"'},

        'local_db_user':        {'Default':   '',
                                 'Validator': lambda value: isinstance(value, str),
                                 'level':     4,
                                 'text':      '访问数据库的用户名，该用户需具备足够的操作权限\n'
                                              '建议通过配置文件配置数据库用户名和密码'},

        'local_db_password':    {'Default':   '',
                                 'Validator': lambda value: isinstance(value, str),
                                 'level':     4,
                                 'text':      '数据库的访问密码\n\n'
                                              '建议通过配置文件配置数据库用户名和密码'},

        'sys_log_file_path':    {'Default':   'syslog/',
                                 'Validator': lambda value: isinstance(value, str),
                                 'level':     4,
                                 'text':      '系统运行日志及错误日志的存储路径\n'},

        'trade_log_file_path':  {'Default':   'tradelog/',
                                 'Validator': lambda value: isinstance(value, str),
                                 'level':     4,
                                 'text':      '明细交易日志的存储路径\n'},

        'trade_log':            {'Default':   True,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     1,
                                 'text':      '是否生成明细交易清单，以pd.DataFrame形式给出明细的每日交易清单\n'
                                              '包括交易信号以及每一步骤的交易结果'},

        'benchmark_asset':      {'Default':   '000300.SH',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and _validate_asset_id(value),
                                 'level':     1,
                                 'text':      '用来产生回测结果评价结果基准收益的资产类型，默认基准为沪深300指数\n'
                                              '基准指数用来生成多用评价结果如alpha、beta比率等，因为这些指标除了考察投资收益的\n'
                                              '绝对值意外，还需要考虑同时期的市场平均表现，只有当投资收益优于市场平均表现的，才会\n'
                                              '被算作超额收益或alpha收益，这才是投资策略追求的目标'},

        'benchmark_asset_type': {'Default':   'IDX',
                                 'Validator': lambda value: _validate_asset_type(value),
                                 'level':     1,
                                 'text':      '基准收益的资产类型，包括：\n'
                                              'IDX  : 指数\n'
                                              'E    : 股票\n'
                                              'FT   : 期货\n'
                                              'FD   : 基金\n'},

        'benchmark_dtype':      {'Default':   'close',
                                 'Validator': lambda value: value in ['open',
                                                                      'high',
                                                                      'low',
                                                                      'close',
                                                                      'vol'],
                                 'level':     1,
                                 'text':      '作为基准收益的资产的价格类型。'},

        'report':               {'Default':   True,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     1,
                                 'text':      '为True时打印运行结果报告\n'
                                              '实时模式显示策略运行报告，'
                                              '回测模式显示回测结果报告，'
                                              '优化模式显示优化结果报告'},

        'visual':               {'Default':   True,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     1,
                                 'text':      '为True时使用图表显示可视化运行结果\n'
                                              '（回测模式显示回测报告，优化模式显示优化结果报告）'},

        'buy_sell_points':      {'Default':   True,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     4,
                                 'text':      '为True时在回测图表中显示买卖点，使用红色和绿色箭头标示出买卖点的位置'},

        'show_positions':       {'Default':   True,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     4,
                                 'text':      '为True时在回测图表中用色带显示投资仓位'},

        'cost_fixed_buy':       {'Default':   0.,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and value >= 0,
                                 'level':     2,
                                 'text':      '买入证券或资产时的固定成本或固定佣金，该金额不随买入金额变化\n'
                                              '默认值为10元'},

        'cost_fixed_sell':      {'Default':   0.,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and value >= 0,
                                 'level':     2,
                                 'text':      '卖出证券或资产时的固定成本或固定佣金，该金额不随卖出金额变化\n'
                                              '默认值为0'},

        'cost_rate_buy':        {'Default':   0.0003,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and 0 <= value < 1,
                                 'level':     1,
                                 'text':      '买入证券或资产时的成本费率或佣金比率，以买入金额的比例计算\n'
                                              '默认值为万分之三'},

        'cost_rate_sell':       {'Default':   0.0001,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and 0 <= value < 1,
                                 'level':     1,
                                 'text':      '卖出证券或资产时的成本费率或佣金比率，以卖出金额的比例计算\n'
                                              '默认值为万分之一'},

        'cost_min_buy':         {'Default':   5.0,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and value >= 0,
                                 'level':     2,
                                 'text':      '买入证券或资产时的最低成本或佣金，买入佣金只能大于或等于该最低金额\n'
                                              '默认值为5元'},

        'cost_min_sell':        {'Default':   0.0,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and value >= 0,
                                 'level':     2,
                                 'text':      '卖出证券或资产时的最低成本或佣金，卖出佣金只能大于或等于该最低金额'},

        'cost_slippage':        {'Default':   0.0,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and 0 <= value < 1,
                                 'level':     2,
                                 'text':      '交易滑点，一个预设参数，模拟由于交易延迟或交易金额过大产生的额外交易成本'},

        'invest_start':         {'Default':   '20160405',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and _is_datelike(value),
                                 'level':     0,
                                 'text':      '回测模式下的回测开始日期\n'
                                              '格式为"YYYYMMDD"'},

        'invest_end':           {'Default':   '20210201',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and _is_datelike(value),
                                 'level':     0,
                                 'text':      '回测模式下的回测结束日期\n'
                                              '格式为"YYYYMMDD"'},

        'invest_cash_amounts':  {'Default':   [100000.0],
                                 'Validator': lambda value: isinstance(value, (tuple, list))
                                                            and all(isinstance(item, (float, int))
                                                                    for item in value)
                                                            and all(item > 1 for item in value),
                                 'level':     1,
                                 'text':      '投资的金额，一个tuple或list，每次投入资金的金额，多个数字表示多次投入'},

        'invest_cash_dates':    {'Default':   None,
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

        'allow_sell_short':     {'Default':   False,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     4,
                                 'text':      '是否允许卖空交易，：\n'
                                              '- False - 默认值，不允许卖空操作，卖出数量最多仅为当前可用持仓数量\n'
                                              '- True -  允许卖空，卖出数量大于持仓量时，即持有空头仓位\n'},

        'long_position_limit':  {'Default':   1.,
                                 'Validator': lambda value: isinstance(value, float) and (value > 0),
                                 'level':     3,
                                 'text':      '回测过程中允许交易信号建立的多头仓位百分比的极限值，即允许动用\n'
                                              '总资产（包括现金和持有股票的总额）的多少百分比用于持有多头仓位，\n'
                                              '默认值1.0，即100%\n'
                                              '如果设置值大于1，则表示允许超过持有现金建仓，这种情况会产生负现金\n'
                                              '余额，表示产生了借贷\n'},

        'short_position_limit': {'Default':  -1.,
                                 'Validator': lambda value: isinstance(value, float) and (value < 0),
                                 'level':     3,
                                 'text':      '回测过程中允许交易信号建立的空头仓位百分比的极限值，即允许持有的\n'
                                              '空头仓位占当前净资产总额的最高比例限额，默认值-1.0，即最多允许借入\n'
                                              '相当于净资产总额100%价值的股票并持有空头仓位，此时持有负股票份额且\n'
                                              '产生正现金流入'},

        'backtest_price_adj':   {'Default':   'back',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and value in ['none', 'n', 'back', 'b', 'adj'],
                                 'level':     4,
                                 'text':      '回测时的复权价格处理方法：\n'
                                              '股票分红除权的处理，正常来说，应该在股票分红除权时计算分红和派息对持仓\n'
                                              '数量和现金的影响，但是目前这种处理方法比较复杂，暂时先采用比较简单的方\n'
                                              '法，即直接采用复权价格进行回测，目前处理方法有两种'
                                              '- none/n - 默认值，不使用复权价格，但也不处理派息，这只是临时处理，因\n'
                                              '           为长期回测不考虑除权派息将会导致回测结果与实际相差巨大\n'
                                              '- back/b - 使用后复权价格回测，可以弥补不考虑分红派股的不足\n'
                                              '- adj    - 使用前复权价格回测。\n'},

        'maximize_cash_usage':  {'Default':   False,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     4,
                                 'text':      '回测交易时是否最大化利用同一批次交易获得的现金。即优先卖出股票并将获得的现金立即\n'
                                              '用于同一批次的买入交易，以便最大限度利用可用现金。当现金的交割期大于0时无效。\n'
                                              '- False - 默认值，同批次买入和卖出信号同时处理，不立即使用卖出资产的现金\n'
                                              '          将同一批次交易委托同时提交时，这是正常情况\n'
                                              '- True -  首先处理同一批次交易中的卖出信号，并在可能时将获得的现金立即用于\n'
                                              '          本次买入'},

        'PT_signal_timing':     {'Default':   'lazy',
                                 'Validator': lambda value: value in ['aggressive', 'lazy'],
                                 'level':     3,
                                 'text':      '回测信号模式为PT（position target）时，控制检查实际持仓比例并自动生成交易\n'
                                              '信号的时机，默认normal\n'
                                              '- aggressive: 在整个策略运行时间点上都会产生交易信号，不论此时PT信号是否发\n'
                                              '              生变化，实时监控实际持仓与计划持仓之间的差异，只要二者发生偏\n'
                                              '              离，就产生信号\n'
                                              '- lazy:       在策略运行时间点上，只有当持仓比例发生变化时，才会产生交易\n'
                                              '              信号，不实时监控实际持仓与计划持仓的差异'},

        'PT_buy_threshold':     {'Default':   0.,
                                 'Validator': lambda value: isinstance(value, (float, int))
                                                            and (0 <= value < 1),
                                 'level':     3,
                                 'text':      '回测信号模式为PT（position target）时，触发买入信号的仓位差异阈值\n'
                                              '在这种模式下，当持有的投资产品的仓位比目标仓位低，且差额超过阈值时，触发买入信号\n'
                                              '例如当卖出阈值为0.05即5%时，若目标持仓30%，那么只有当实际持仓<=25%时，才会产生\n'
                                              '交易信号，即此时实际持仓与目标持仓之间的差值大于5%了'},

        'PT_sell_threshold':    {'Default':   0.,
                                 'Validator': lambda value: isinstance(value, (float, int))
                                                            and (0 <= value < 1),
                                 'level':     3,
                                 'text':      '回测信号模式为PT（position target）时，触发卖出信号的仓位差异阈值\n'
                                              '在这种模式下，当持有的投资产品的仓位比目标仓位高，且差额超过阈值时，触发卖出信号\n'
                                              '例如当卖出阈值为0.05即5%时，若目标持仓30%，那么只有当实际持仓>=35%时，才会产生\n'
                                              '交易信号，即此时实际持仓与目标持仓之间的差值大于5%了'},

        'price_priority_OHLC':  {'Default':   'OHLC',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and all(item.upper() in 'OHLC'
                                                                    for item in value)
                                                            and all(item.upper() in value
                                                                    for item in 'OHLC'),
                                 'level':     3,
                                 'text':      '回测时如果存在多种价格类型的交易信号，而且交易价格的类型为OHLC时，处理各种\n'
                                              '不同的价格信号的优先级。\n'
                                              '输入类型为字符串，包括O、H、L、C四个字母的所有可能组合'},

        'price_priority_quote': {'Default':   'normal',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and (value in ['normal', 'reverse']),
                                 'level':     3,
                                 'text':      '回测时如果存在多种价格类型的交易信号，而且交易价格的类型为实时报价时，回测程序处理\n'
                                              '不同的价格信号的优先级。\n'
                                              '输入包括"normal" 以及 "reverse"两种，分别表示：\n'
                                              '- "normal"：  优先处理更接近成交价的报价，如卖1/买1等\n'
                                              '- "reverse"： 优先处理更远离成交价的报价，如卖5/买5等'},

        'cash_deliver_period':  {'Default':   0,
                                 'Validator': lambda value: isinstance(value, int)
                                                            and value in range(5),
                                 'level':     3,
                                 'text':      '回测时卖出股票获得现金的交割周期，用一个数字N代表交易日后第N天可以完成现金交割。\n'
                                              '获得现金后立即计入总资产，但在途资金（尚未交割的资金）不能用于下一笔交易\n'
                                              '当现金交割期为零时，可以选择在同一轮交易中先卖出资产获得尽可能多的现金用于本轮\n'
                                              '买入'},

        'stock_deliver_period': {'Default':   1,
                                 'Validator': lambda value: isinstance(value, int)
                                                            and value in range(5),
                                 'level':     3,
                                 'text':      '回测时买入股票后的股票交割周期，用一个数字N代表交易日后第N天可以完成资产交割。\n'
                                              '获得股票后立即计入总资产，但尚未交割的股票不能用于下一笔交易'},

        'opti_start':           {'Default':   '20160405',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and _is_datelike(value),
                                 'level':     0,
                                 'text':      '优化模式下的策略优化区间开始日期'},

        'opti_end':             {'Default':   '20191231',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and _is_datelike(value),
                                 'level':     0,
                                 'text':      '优化模式下的策略优化区间结束日期'},

        'opti_cash_amounts':    {'Default':   [100000.0],
                                 'Validator': lambda value: isinstance(value, (tuple, list))
                                                            and all(isinstance(item, (float, int))
                                                                    for item in value)
                                                            and all(item > 1 for item in value),
                                 'level':     1,
                                 'text':      '优化模式投资的金额，一个tuple或list，每次投入资金的金额，多个数字表示多次投入'},

        'opti_cash_dates':      {'Default':   None,
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

        'opti_type':            {'Default':   'single',
                                 'Validator': lambda value: isinstance(value, str) and value in ['single', 'multiple'],
                                 'level':     3,
                                 'text':      '优化类型。指优化数据的利用方式:\n'
                                              '"single"   - 在每一回合的优化测试中，在优化区间上进行覆盖整个区间的单次回测并评价\n'
                                              '             回测结果\n'
                                              '"multiple" - 在每一回合的优化测试中，将优化区间的数据划分为多个子区间，在这些子\n'
                                              '             区间上分别测试，并根据所有测试的结果确定策略在整个区间上的评价结果'},

        'opti_sub_periods':     {'Default':   5,
                                 'Validator': lambda value: isinstance(value, int) and value >= 1,
                                 'level':     3,
                                 'text':      '仅对无监督优化有效。且仅当优化类型为"multiple"时有效。将优化区间切分为子区间的数量'},

        'opti_sub_prd_length':  {'Default':   0.6,
                                 'Validator': lambda value: isinstance(value, float) and 0 <= value <= 1.,
                                 'level':     3,
                                 'text':      '仅当优化类型为"multiple"时有效。每一个优化子区间长度占整个优化区间长度的比例\n'
                                              '例如，当优化区间长度为10年时，本参数为0.6代表每一个优化子区间长度为6年'},

        'test_start':           {'Default':   '20200106',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and _is_datelike(value),
                                 'level':     0,
                                 'text':      '优化模式下的策略测试区间开始日期'
                                              '格式为"YYYYMMDD"'
                                              '字符串类型输入'},

        'test_end':             {'Default':   '20210201',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and _is_datelike(value),
                                 'level':     0,
                                 'text':      '优化模式下的策略测试区间结束日期\n'
                                              '格式为"YYYYMMDD"'
                                              '字符串类型输入'},

        'test_cash_amounts':    {'Default':   [100000.0],
                                 'Validator': lambda value: isinstance(value, (tuple, list))
                                                            and all(isinstance(item, (float, int))
                                                                    for item in value)
                                                            and all(item > 1 for item in value),
                                 'level':     1,
                                 'text':      '优化模式策略测试投资的金额，一个tuple或list，每次投入资金的金额。\n'
                                              '模拟现金多次定投投入时，输入多个数字表示多次投入\n'
                                              '输入的数字的个数必须与cash_dates中的日期数量相同'},

        'test_cash_dates':      {'Default':   None,
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

        'test_type':            {'Default':   'single',
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

        'test_indicators':      {'Default':   'years,fv,return,mdd,v,ref,alpha,beta,sharp,info',
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

        'indicator_plot_type':  {'Default':   'histo',
                                 'Validator': lambda value: _validate_indicator_plot_type(value),
                                 'level':     2,
                                 'text':      '优化或测试结果评价指标的可视化图表类型:\n'
                                              '0  - errorbar 类型\n'
                                              '1  - scatter 类型\n'
                                              '2  - histo 类型\n'
                                              '3  - violin 类型\n'
                                              '4  - box 类型'},

        'test_sub_periods':     {'Default':   3,
                                 'Validator': lambda value: isinstance(value, int) and value >= 1,
                                 'level':     3,
                                 'text':      '仅当测试类型为"multiple"时有效。将测试区间切分为子区间的数量'},

        'test_sub_prd_length':  {'Default':   0.75,
                                 'Validator': lambda value: isinstance(value, float) and 0 <= value <= 1.,
                                 'level':     3,
                                 'text':      '仅当测试类型为"multiple"时有效。每一个测试子区间长度占整个测试区间长度的比例\n'
                                              '例如，当测试区间长度为4年时，本参数0.75代表每个测试子区间长度为3年'},

        'test_cycle_count':     {'Default':   100,
                                 'Validator': lambda value: isinstance(value, int) and value >= 1,
                                 'level':     3,
                                 'text':      '仅当测试类型为"montecarlo"时有效。生成的模拟测试数据的数量。\n'
                                              '默认情况下生成100组模拟价格数据，并进行100次策略回测并评价其统计结果'},

        'optimize_target':      {'Default':   'final_value',
                                 'Validator': lambda value: isinstance(value, str)
                                                            and value in ['final_value', 'FV', 'SHARP'],
                                 'level':     1,
                                 'text':      '策略的优化目标。即优化时以找到该指标最佳的策略为目标'},

        'maximize_target':      {'Default':   True,
                                 'Validator': lambda value: isinstance(value, bool),
                                 'level':     1,
                                 'text':      '为True时寻找目标值最大的策略，为False时寻找目标值最低的策略'},

        'opti_method':          {'Default':   1,
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

        'opti_grid_size':       {'Default':   1,
                                 'Validator': lambda value: _num_or_seq_of_num(value) and value > 0,
                                 'level':     3,
                                 'text':      '使用穷举法搜索最佳策略时有用，搜索步长'},

        'opti_sample_count':    {'Default':   256,
                                 'Validator': lambda value: isinstance(value, int) and value > 0,
                                 'level':     3,
                                 'text':      '使用蒙特卡洛法搜索最佳策略时有用，在向量空间中采样的数量'},

        'opti_r_sample_count':  {'Default':   16,
                                 'Validator': lambda value: _num_or_seq_of_num(value)
                                                            and value >= 0,
                                 'level':     3,
                                 'text':      '在使用递进步长法搜索最佳策略时有用，每一轮随机取样的数量'},

        'opti_reduce_ratio':    {'Default':   0.1,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and 0 < value < 1,
                                 'level':     3,
                                 'text':      '在使用递进步长法搜索最佳策略时有用，\n'
                                              '每一轮随机取样后择优留用的比例，同样也是子空间缩小的比例\n'},

        'opti_max_rounds':      {'Default':   5,
                                 'Validator': lambda value: isinstance(value, int)
                                                            and value > 1,
                                 'level':     3,
                                 'text':      '在使用递进步长法搜索最佳策略时有用，多轮搜索的最大轮数，轮数大于该值时停止搜索'},

        'opti_min_volume':      {'Default':   1000,
                                 'Validator': lambda value: isinstance(value, (float, int))
                                                            and value > 0,
                                 'level':     3,
                                 'text':      '在使用递进步长法搜索最佳策略时有用，空间最小体积，当空间volume低于该值时停止搜索'},

        'opti_population':      {'Default':   1000.0,
                                 'Validator': lambda value: isinstance(value, float)
                                                            and value >= 0,
                                 'level':     3,
                                 'text':      '在使用遗传算法搜索最佳策略时有用，种群的数量'},

        'opti_output_count':    {'Default':   30,
                                 'Validator': lambda value: isinstance(value, int)
                                                            and value > 0,
                                 'level':     3,
                                 'text':      '策略参数优化后输出的最优参数数量'},

    }
    _validate_vkwargs_dict(vkwargs)

    return vkwargs


def _validate_vkwargs_dict(vkwargs):
    """ Check that we didn't make a typo in any of the things
        that should be the same for all vkwargs dict items:

    :param vkwargs:
    :return:
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


def _vkwargs_to_text(kwargs, level=0, info=False, verbose=False):
    """ Given a list of kwargs, verify that all kwargs are in the valid kwargs,
        and display their values and other information according to given
        parameters. return a string with all formulated information

    :param kwargs: list or tuple, kwargs that are to be displayed
    :param level: int or list of ints, 所有需要输出的kwargs的层级
    :param info:
    :param verbose:
    :return:
    """
    from qteasy.utilfuncs import reindent
    if isinstance(level, int):
        levels = [level]
    elif isinstance(level, list):
        levels = level
    else:
        raise TypeError(f'level should be an integer or list of integers, got {type(level)}')
    assert all(isinstance(item, int) for item in levels), f'TypeError, levels should be a list of integers'
    column_w_key = 22
    column_w_current = 15
    column_offset_description = 4
    vkwargs = _valid_qt_kwargs()
    output_strings = list()
    if info:
        output_strings.append('No. Config-Key            Cur Val        Default val\n')
        if verbose:
            output_strings.append('      Description\n')
        output_strings.append('----------------------------------------------------\n')
    else:
        output_strings.append('No. Config-Key            Cur Val        \n')
        output_strings.append('-----------------------------------------\n')
    no = 0
    for key in kwargs:
        if key not in vkwargs:
            from qteasy import logger_core
            logger_core.warning(f'Unrecognized config_key={str(key)}')
            cur_value = str(QT_CONFIG[key])
            default_value = 'N/A'
            description = 'Customer defined argument key'
        else:
            cur_level = vkwargs[key]['level']
            if cur_level in levels:  # only display kwargs that are in the list of levels
                cur_value = str(QT_CONFIG[key])
                default_value = str(vkwargs[key]['Default'])
                description = str(vkwargs[key]['text'])
            else:
                continue

        no += 1
        output_strings.append(f'{no: <4}')
        output_strings.append(f'{str(key): <{column_w_key}}')
        if info:
            output_strings.append(f'{cur_value: <{column_w_current}}'
                                  f'<{default_value}>\n')
            if verbose:
                output_strings.append(f'{reindent(description, 6): <{column_w_key + column_w_current * 2}}\n\n')
        else:
            output_strings.append(f'{cur_value}\n')
    return ''.join(output_strings)


def _initialize_config_kwargs(kwargs, vkwargs):
    """ Given a "valid kwargs table" and some kwargs, verify that each key-word
        is valid per the kwargs table, and that the value of the config_key is the
        correct type.  Fill a configuration dictionary with the default value
        for each config_key, and then substitute in any values that were provided
        as kwargs and return the configuration dictionary.

    :param kwargs: keywords that is given by user
    :param vkwargs: valid keywords table usd for validating given kwargs
    :return:
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

    :param config: configuration dictionary to be updated
    :param kwargs: kwargs that are to be updated
    :param raise_if_key_not_existed:  if True, raise when key does not exist in vkwargs
    :return:
        config_key ConfigDict
    """
    vkwargs = _valid_qt_kwargs()
    for key in kwargs.keys():
        value = _parse_string_kwargs(kwargs[key], key, vkwargs)
        if _validate_key_and_value(key, value, raise_if_key_not_existed):
            config[key] = value

    return config


def _parse_string_kwargs(value, key, vkwargs):
    """ correct the type of value to the same of default type

    :param value:
    :param key:
    :param vkwargs:
    :return:
    """
    # 为防止value的类型不正确，将value修改为正确的类型，与 vkwargs 的
    # Default value 的类型相同
    if key not in vkwargs:
        return value
    if not isinstance(value, str):
        return value
    default_value = vkwargs[key]['Default']
    if (not isinstance(default_value, str)) and (default_value is not None):
        import ast
        value = ast.literal_eval(value)
    return value


def _validate_key_and_value(key, value, raise_if_key_not_existed=False):
    """ given one key, validate the value according to vkwargs dict
        return True if the value is valid
        raise if the value is not valid
        return False or raise if the key does not exist in vkwargs, depending on
        argument "raise_if_key_not_existed"

    :param key:
    :param value:
    :param raise_if_key_not_existed:    when key does not exist in vkwargs:
                                        raise if True,
                                        return False if False and warning
    :return:
    """
    vkwargs = _valid_qt_kwargs()
    if (key not in vkwargs) and raise_if_key_not_existed:
        err_msg = f'config_key <{key}> is not a built-in parameter key, please check your input!'
        raise KeyError(err_msg)
    if key not in vkwargs:
        # warning is suppressed, ignore warning
        # warn_msg = f'config_key <{key}> is not a built-in parameter key, but might be acceptable because the error ' \
        #            f'is suppressed by program!'
        # warnings.warn(warn_msg)
        return True

    try:
        valid = vkwargs[key]['Validator'](value)
    except Exception as ex:
        ex.extra_info = f'config_key {key} validator raised exception to value: {str(value)}'
        raise ex
    if not valid:
        import inspect
        v = inspect.getsource(vkwargs[key]['Validator']).strip()
        raise TypeError(
                f'config_key {key} validator returned False for value: {str(value)} of type {type(value)}\n'
                f'Extra information: \n{vkwargs[key]["text"]}\n    ' + v)
        # ---------------------------------------------------------------
        #      至此 , 如果没有任何Exception被Raise出来,
        #      那么我们就认为所有的argument都是valid的.

    return True


def _validate_asset_id(value):
    """

    :param value:
    :return:
    """
    return True


def _validate_indicator_plot_type(value):
    """ validate the value of indicator plot types, which include:

    '优化或测试结果评价指标的可视化图表类型:\n'
         '0  - errorbar 类型\n'
         '1  - scatter 类型\n'
         '2  - histo 类型\n'
         '3  - violin 类型\n'
         '4  - box 类型'

    :param value:
    :return: Boolean
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


def _validate_asset_type(value):
    """

    :param value:
    :return:
    """
    from .utilfuncs import AVAILABLE_ASSET_TYPES
    return value in AVAILABLE_ASSET_TYPES


def _is_datelike(value):
    if isinstance(value, (pd.Timestamp, datetime.datetime, datetime.date)):
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
        the validation is too complex to make it worth while,
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


def _validate_asset_pool(kwargs):
    """

    :param kwargs:
    :return:
    """
    return True


QT_CONFIG = _initialize_config_kwargs({}, _valid_qt_kwargs())