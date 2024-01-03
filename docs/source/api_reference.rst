配置QTEASY
==============

查看qteasy的配置信息:

.. autofunction:: qteasy.configuration

.. autofunction:: qteasy.get_config

.. autofunction:: qteasy.get_configurations

修改qteasy的配置信息:

.. autofunction:: qteasy.configure

.. autofunction:: qteasy.set_config

将所有的配置变量重置为默认值:

.. autofunction:: qteasy.reset_config

从文件中读取配置信息:

.. autofunction:: qteasy.load_config

将配置信息写入文件:

.. autofunction:: qteasy.save_config

qteasy的所有配置变量
-----------------------

下面是qteasy的配置变量，可以通过qteasy.get_config()函数查看当前的配置信息，也可以通过qteasy.configure()函数修改配置信息。

.. list-table:: qteasy Configuration Variables
   :widths: 25 25 25 50
   :header-rows: 1

   * - Name
     - Level
     - Default Value
     - Description
   * - mode
     - 0
     - 1
     - | qteasy 的运行模式:
       | 0: 实盘运行模式
       | 1: 回测-评价模式
       | 2: 策略优化模式
       | 3: 统计预测模式
   * - time_zone
     - 4
     - local
     - | 回测时的时区，默认值"local"，表示使用本地时区。
       | 如果需要固定时区，设置任意合法的时区，例如：
       | Asia/Shanghai
       | Asia/Hong_Kong
       | US/Eastern
       | US/Pacific
       | Europe/London
       | Europe/Paris
       | Australia/Sydney
       | Australia/Melbourne
       | Pacific/Auckland
       | Pacific/Chatham
       | etc.
   * - asset_pool
     - 0
     - 000300.SH
     - 可用投资产品池，投资组合基于池中的产品创建
   * - asset_type
     - 0
     - IDX
     - | 投资产品的资产类型，包括：
       | IDX  : 指数
       | E    : 股票
       | FT   : 期货
       | FD   : 基金
   * - live_trade_account_id
     - 0
     - None
     - | 实盘交易账户ID，用于实盘交易，如果指定了该参数，则会直接
       | 使用该账户，除非账户不存在
   * - live_trade_account
     - 0
     - None
     - | 实盘交易账户名称，用于实盘交易，如果指定了该参数，则会查找该
       | 账户对应的account_id并使用该账户，除非账户不存在
   * - live_trade_debug_mode
     - 1
     - False
     - 实盘交易调试模式，True: 调试模式，False: 正常模式
   * - live_trade_init_cash
     - 1
     - 1000000.0
     - | 实盘交易账户的初始资金，浮点数，例如：
       | 1000000.0 : 初始资金为100万
       | 1000000   : 初始资金为100万
   * - live_trade_init_holdings
     - 1
     - None
     - | 实盘交易账户的初始持仓，字典，例如：
       | {'000001.SZ': 1000, '000002.SZ': 2000} : 初始持仓为
       | 000001.SZ: 1000股, 000002.SZ: 2000股
   * - live_trade_broker_type
     - 1
     - simulator
     - | 实盘交易账户的交易代理商类型，可以设置为模拟交易代理商返回交易结果、手动输入结果或者连接到交易代理商的交易接口
       | 默认使用模拟交易代理Simulator
   * - live_trade_broker_params
     - 1
     - None
     - | 实盘交易账户的交易代理商参数，字典，例如：
       | {'host': 'localhost', 'port': 8888} : 交易代理商的主机名和端口号
       | 具体的参数设置请参考交易代理商的文档
       | 如果使用 'simulator' broker，且设置此参数为None，则会使用config中的
       | backtest参数
   * - live_price_acquire_channel
     - 2
     - eastmoney
     - | 实盘交易时获取实时价格的方式：
       | eastmoney - 通过东方财富网获取实时价格
       | tushare  - 通过tushare获取实时价格(需要自行开通权限)
       | akshare  - Not Implemented: 从akshare获取实时价格
   * - live_price_acquire_freq
     - 2
     - 15MIN
     - | 实盘交易时获取实时价格的频率：
       | H      - 每1小时获取一次数据
       | 30MIN  - 每30分钟获取一次数据
       | 15MIN  - 每15分钟获取一次数据
       | 5MIN   - 每5分钟获取一次数据
       | 1MIN   - 每1分钟获取一次数据
   * - watched_price_refresh_interval
     - 4
     - 5
     - | 实盘交易时监看实时价格的刷新频率，单位为秒，默认为5秒
       | 该数值不能低于5秒
   * - trade_batch_size
     - 0
     - 0.0
     - | 投资产品的最小申购批量大小，浮点数，例如：
       | 0. : 可以购买任意份额的投资产品，包括小数份额
       | 1. : 只能购买整数份额的投资产品
       | 100: 可以购买100的整数倍份额投资产品
       | n  : 可以购买的投资产品份额为n的整数倍，n不必为整数
   * - sell_batch_size
     - 0
     - 0.0
     - | 投资产品的最小卖出或赎回批量大小，浮点数，例如：
       | 0. : 可以购买任意份额的投资产品，包括小数份额
       | 1. : 只能购买整数份额的投资产品
       | 100: 可以购买100的整数倍份额投资产品
       | n  : 可以购买的投资产品份额为n的整数倍，n不必为整数
   * - cash_decimal_places
     - 2
     - 2
     - | 现金的小数位数，例如：
       | 0: 现金只能为整数
       | 2: 保留小数点后两位数字
   * - amount_decimal_places
     - 2
     - 2
     - | 投资产品的份额的小数位数，例如：
       | 0: 份额只能为整数
       | 2: 保留小数点后两位数字
   * - riskfree_ir
     - 1
     - 0.0035
     - 无风险利率，如果选择"考虑现金的时间价值"，则回测时现金按此年利率增值
   * - parallel
     - 1
     - True
     - 如果True，策略参数寻优时将利用多核心CPU进行并行计算提升效率
   * - hist_dnld_parallel
     - 4
     - 16
     - 下载历史数据时启用的线程数量，为0或1时采用单线程下载，大于1时启用多线程
   * - hist_dnld_delay
     - 4
     - 0.0
     - 为防止服务器数据压力过大，下载历史数据时下载一定数量的数据后延迟的时间长度，单位为秒
   * - hist_dnld_delay_evy
     - 4
     - 0
     - | 为防止服务器数据压力过大，下载历史数据时，每下载一定数量的数据，就延迟一段时间。
       | 此参数为两次延迟之间的数据下载量
   * - hist_dnld_prog_bar
     - 4
     - False
     - 下载历史数据时是否显示进度条
   * - hist_dnld_retry_cnt
     - 4
     - 7
     - 下载历史数据失败时的自动重试次数
   * - hist_dnld_retry_delay
     - 4
     - 1.0
     - 下载历史数据失败时的自动重试前的延迟时间，单位为秒
   * - hist_dnld_backoff
     - 4
     - 2.0
     - | 下载历史数据失败时的自动重试的延迟时间倍增乘数
       | 例如，设置hist_dnld_backoff = 2时，每次重试失败
       | 后延迟时间会变为前一次的2倍
   * - auto_dnld_hist_tables
     - 4
     - []
     - | 在实盘运行时自动下载的历史数据表名列表，例如：
       | ["stock_daily", "index_weekly", "stock_monthly"]
       | 如果列表为空，则不自动下载任何历史数据
   * - gpu
     - 4
     - False
     - | 如果True，策略参数寻优时使用GPU加速计算
       | <本功能目前尚未实现! NotImplemented>
   * - local_data_source
     - 1
     - file
     - | 确定本地历史数据存储方式：
       | file     - 历史数据以本地文件的形式存储，
       |            文件格式在"local_data_file_type"属性中指定，包括csv/hdf等多种选项
       | database - 历史数据存储在一个mysql数据库中
       |            选择此选项时，需要在配置文件中配置数据库的连接信息
       | db       - 等同于"database"
   * - local_data_file_type
     - 4
     - csv
     - | 确定本地历史数据文件的存储格式：
       | csv - 历史数据文件以csv形式存储，速度较慢但可以用Excel打开
       | hdf - 历史数据文件以hd5形式存储，数据存储和读取速度较快
       | feather/fth - 历史数据文件以feather格式存储，数据交换速度快但不适用长期存储
   * - local_data_file_path
     - 4
     - data/
     - 确定本地历史数据文件存储路径
   * - local_db_host
     - 4
     - localhost
     - 用于存储历史数据的数据库的主机名，该数据库应该为mysql数据库或MariaDB
   * - local_db_port
     - 4
     - 3306
     - 用于存储历史数据的数据库的端口号，默认值为mysql数据库的端口号3306
   * - local_db_name
     - 4
     - qt_db
     - 用于存储历史数据的数据库名，默认值为"qt_db"
   * - local_db_user
     - 4
     -
     - | 访问数据库的用户名，该用户需具备足够的操作权限
       | 建议通过配置文件配置数据库用户名和密码
   * - local_db_password
     - 4
     -
     - | 数据库的访问密码
       | 建议通过配置文件配置数据库用户名和密码
   * - sys_log_file_path
     - 4
     - syslog/
     - 系统运行日志及错误日志的存储路径
   * - trade_log_file_path
     - 4
     - tradelog/
     - 明细交易日志的存储路径
   * - trade_log
     - 1
     - True
     - | 是否生成明细交易清单，以pd.DataFrame形式给出明细的每日交易清单
       | 包括交易信号以及每一步骤的交易结果
   * - benchmark_asset
     - 1
     - 000300.SH
     - | 用来产生回测结果评价结果基准收益的资产类型，默认基准为沪深300指数
       | 基准指数用来生成多用评价结果如alpha、beta比率等，因为这些指标除了考察投资收益的
       | 绝对值意外，还需要考虑同时期的市场平均表现，只有当投资收益优于市场平均表现的，才会
       | 被算作超额收益或alpha收益，这才是投资策略追求的目标
   * - benchmark_asset_type
     - 1
     - IDX
     - | 基准收益的资产类型，包括：
       | IDX  : 指数
       | E    : 股票
       | FT   : 期货
       | FD   : 基金
   * - benchmark_dtype
     - 1
     - close
     - 作为基准收益的资产的价格类型。
   * - report
     - 1
     - True
     - | 为True时打印运行结果报告
       | 实时模式显示策略运行报告，回测模式显示回测结果报告，优化模式显示优化结果报告
   * - visual
     - 0
     - True
     - | 为True时使用图表显示可视化运行结果
       | （回测模式显示回测报告，优化模式显示优化结果报告）
   * - buy_sell_points
     - 4
     - True
     - 为True时在回测图表中显示买卖点，使用红色和绿色箭头标示出买卖点的位置
   * - show_positions
     - 4
     - True
     - 为True时在回测图表中用色带显示投资仓位
   * - cost_fixed_buy
     - 2
     - 0.0
     - | 买入证券或资产时的固定成本或固定佣金，该金额不随买入金额变化
       | 默认值为10元
   * - cost_fixed_sell
     - 2
     - 0.0
     - | 卖出证券或资产时的固定成本或固定佣金，该金额不随卖出金额变化
       | 默认值为0
   * - cost_rate_buy
     - 1
     - 0.0003
     - | 买入证券或资产时的成本费率或佣金比率，以买入金额的比例计算
       | 默认值为万分之三
   * - cost_rate_sell
     - 1
     - 0.0001
     - | 卖出证券或资产时的成本费率或佣金比率，以卖出金额的比例计算
       | 默认值为万分之一
   * - cost_min_buy
     - 2
     - 5.0
     - | 买入证券或资产时的最低成本或佣金，买入佣金只能大于或等于该最低金额
       | 默认值为5元
   * - cost_min_sell
     - 2
     - 5.0
     - 卖出证券或资产时的最低成本或佣金，卖出佣金只能大于或等于该最低金额
   * - cost_slippage
     - 2
     - 0.0
     - 交易滑点，一个预设参数，模拟由于交易延迟或交易金额过大产生的额外交易成本
   * - invest_start
     - 0
     - 20160405
     - | 回测模式下的回测开始日期
       | 格式为"YYYYMMDD"
   * - invest_end
     - 0
     - 20210201
     - | 回测模式下的回测结束日期
       | 格式为"YYYYMMDD"
   * - invest_cash_amounts
     - 1
     - [100000.0]
     - 投资的金额，一个tuple或list，每次投入资金的金额，多个数字表示多次投入
   * - invest_cash_dates
     - 2
     - None
     - | 回测操作现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None
       | 当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖
       | invest_start
       | 参数输入类型为str时，格式为"YYYYMMDD"
       | 如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型
       | 以下两种输入方式等效：
       | "20100104,20100202,20100304" =
       | ["20100104", "20100202", "20100304"]
   * - allow_sell_short
     - 4
     - False
     - | 是否允许卖空交易，：
       | False - 默认值，不允许卖空操作，卖出数量最多仅为当前可用持仓数量
       | True -  允许卖空，卖出数量大于持仓量时，即持有空头仓位
   * - long_position_limit
     - 3
     - 1.0
     - | 回测过程中允许交易信号建立的多头仓位百分比的极限值，即允许动用
       | 总资产（包括现金和持有股票的总额）的多少百分比用于持有多头仓位，
       | 默认值1.0，即100%
       | 如果设置值大于1，则表示允许超过持有现金建仓，这种情况会产生负现金
       | 余额，表示产生了借贷
   * - short_position_limit
     - 3
     - -1.0
     - | 回测过程中允许交易信号建立的空头仓位百分比的极限值，即允许持有的
       | 空头仓位占当前净资产总额的最高比例限额，默认值-1.0，即最多允许借入
       | 相当于净资产总额100%价值的股票并持有空头仓位，此时持有负股票份额且
       | 产生正现金流入
   * - backtest_price_adj
     - 4
     - none
     - | 回测时的复权价格处理方法：
       | 股票分红除权的处理，正常来说，应该在股票分红除权时计算分红和派息对持仓
       | 数量和现金的影响，但是目前这种处理方法比较复杂，暂时先采用比较简单的方
       | 法，即直接采用复权价格进行回测，目前处理方法有两种
       | - none/n - 默认值，不使用复权价格，但也不处理派息，这只是临时处理，因
       |            为长期回测不考虑除权派息将会导致回测结果与实际相差巨大
       | - back/b - 使用后复权价格回测，可以弥补不考虑分红派股的不足
       | - adj    - 使用前复权价格回测。
   * - maximize_cash_usage
     - 4
     - True
     - | 回测交易时是否最大化利用同一批次交易获得的现金。即优先卖出股票并将获得的现金立即
       | 用于同一批次的买入交易，以便最大限度利用可用现金。当现金的交割期大于0时无效。
       | - True -  默认值，首先处理同一批次交易中的卖出信号，并在可能时将获得的现金
       |           立即用于本次买入
       | - False - 同批次买入和卖出信号同时处理，不立即使用卖出资产的现金将同一批
       |           次交易委托同时提交时，这是正常情况
   * - PT_signal_timing
     - 3
     - lazy
     - | 回测信号模式为PT（position target）时，控制检查实际持仓比例并自动生成交易
       | 信号的时机，默认normal
       | - aggressive: 在整个策略运行时间点上都会产生交易信号，不论此时PT信号是否发
       |               生变化，实时监控实际持仓与计划持仓之间的差异，只要二者发生偏
       |               离，就产生信号
       | - lazy:       在策略运行时间点上，只有当持仓比例发生变化时，才会产生交易
       |               信号，不实时监控实际持仓与计划持仓的差异
   * - PT_buy_threshold
     - 3
     - 0.0
     - | 回测信号模式为PT（position target）时，触发买入信号的仓位差异阈值
       | 在这种模式下，当持有的投资产品的仓位比目标仓位低，且差额超过阈值时，触发买入信号
       | 例如当卖出阈值为0.05即5%时，若目标持仓30%，那么只有当实际持仓<=25%时，才会产生
       | 交易信号，即此时实际持仓与目标持仓之间的差值大于5%了
   * - PT_sell_threshold
     - 3
     - 0.0
     - | 回测信号模式为PT（position target）时，触发卖出信号的仓位差异阈值
       | 在这种模式下，当持有的投资产品的仓位比目标仓位高，且差额超过阈值时，触发卖出信号
       | 例如当卖出阈值为0.05即5%时，若目标持仓30%，那么只有当实际持仓>=35%时，才会产生
       | 交易信号，即此时实际持仓与目标持仓之间的差值大于5%了
   * - price_priority_OHLC
     - 3
     - OHLC
     - | 回测时如果存在多种价格类型的交易信号，而且交易价格的类型为OHLC时，处理各种
       | 不同的价格信号的优先级。
       | 输入类型为字符串，O、H、L、C、A分别代表Open,High,Low,Close,Nav
   * - price_priority_quote
     - 3
     - normal
     - | 回测时如果存在多种价格类型的交易信号，而且交易价格的类型为实时报价时，回测程序处理
       | 不同的价格信号的优先级。
       | 输入包括"normal" 以及 "reverse"两种，分别表示：
       | - "normal"：  优先处理更接近成交价的报价，如卖1/买1等
       | - "reverse"： 优先处理更远离成交价的报价，如卖5/买5等
   * - cash_delivery_period
     - 3
     - 0
     - | 回测时卖出股票获得现金的交割周期，用一个数字N代表交易日后第N天可以完成现金交割。
       | 获得现金后立即计入总资产，但在途资金（尚未交割的资金）不能用于下一笔交易
       | 当现金交割期为零时，可以选择在同一轮交易中先卖出资产获得尽可能多的现金用于本轮
       | 买入
   * - stock_delivery_period
     - 3
     - 1
     - | 回测时买入股票后的股票交割周期，用一个数字N代表交易日后第N天可以完成资产交割。
       | 获得股票后立即计入总资产，但尚未交割的股票不能用于下一笔交易
   * - market_open_time_am
     - 3
     - 09:30:00
     - 交易市场上午开市时间
   * - market_close_time_am
     - 3
     - 11:30:00
     - 交易市场上午收市时间
   * - market_open_time_pm
     - 3
     - 13:00:00
     - 交易市场下午开市时间
   * - market_close_time_pm
     - 3
     - 15:00:00
     - 交易市场下午收市时间
   * - strategy_open_close_timing_offset
     - 3
     - 1
     - | 策略信号的开盘/收盘运行时间偏移量，单位为分钟，当策略信号运行时机为开盘/收盘，需要提前/推迟
       | 一个偏移量运行，避免无法交易。
   * - opti_start
     - 0
     - 20160405
     - 优化模式下的策略优化区间开始日期
   * - opti_end
     - 0
     - 20191231
     - 优化模式下的策略优化区间结束日期
   * - opti_cash_amounts
     - 1
     - [100000.0]
     - 优化模式投资的金额，一个tuple或list，每次投入资金的金额，多个数字表示多次投入
   * - opti_cash_dates
     - 2
     - None
     - | 策略优化区间现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None
       | 当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖
       | invest_start
       | 参数输入类型为str时，格式为"YYYYMMDD"
       | 如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型
       | 以下两种输入方式等效：
       | "20100104,20100202,20100304"["20100104", "20100202", "20100304"]
   * - opti_type
     - 3
     - single
     - | 优化类型。指优化数据的利用方式:
       | "single"   - 在每一回合的优化测试中，在优化区间上进行覆盖整个区间的单次回测并评价
       |              回测结果
       | "multiple" - 在每一回合的优化测试中，将优化区间的数据划分为多个子区间，在这些子
       |              区间上分别测试，并根据所有测试的结果确定策略在整个区间上的评价结果
   * - opti_sub_periods
     - 3
     - 5
     - 仅对无监督优化有效。且仅当优化类型为"multiple"时有效。将优化区间切分为子区间的数量
   * - opti_sub_prd_length
     - 3
     - 0.6
     - | 仅当优化类型为"multiple"时有效。每一个优化子区间长度占整个优化区间长度的比例
       | 例如，当优化区间长度为10年时，本参数为0.6代表每一个优化子区间长度为6年
   * - test_start
     - 0
     - 20200106
     - 优化模式下的策略测试区间开始日期格式为"YYYYMMDD"字符串类型输入
   * - test_end
     - 0
     - 20210201
     - | 优化模式下的策略测试区间结束日期
       | 格式为"YYYYMMDD"字符串类型输入
   * - test_cash_amounts
     - 1
     - [100000.0]
     - | 优化模式策略测试投资的金额，一个tuple或list，每次投入资金的金额。
       | 模拟现金多次定投投入时，输入多个数字表示多次投入
       | 输入的数字的个数必须与cash_dates中的日期数量相同
   * - test_cash_dates
     - 2
     - None
     - | 策略优化区间现金投入的日期，一个str或list，多个日期表示多次现金投入。默认为None
       | 当此参数为None时，现金投入日期与invest_start相同，当参数不为None时，此参数覆盖
       | invest_start参数|
       | 参数输入类型为str时，格式为"YYYYMMDD"
       | 如果需要模拟现金多次定投投入，或者多次分散投入，则可以输入list类型或str类型
       | 以下两种输入方式等效：
       | "20100104,20100202,20100304"["20100104", "20100202", "20100304"]
   * - test_type
     - 3
     - single
     - | 测试类型。指测试数据的利用方式:
       | "single"     - 在每一回合的优化测试中，在测试区间上进行覆盖整个区间的单次回测
       |                并评价回测结果
       | "multiple"   - 在每一回合的优化测试中，将测试区间的数据划分为多个子区间，在这
       |                些子区间上分别测试，并根据所有测试的结果确定策略在整个区间上的
       |                评价结果
       | "montecarlo" - 蒙特卡洛测试，根据测试区间历史数据的统计性质，随机生成大量的模
       |                拟价格变化数据，用这些数据对策略的表现进行评价，最后给出统计意
       |                义的评价结果
   * - test_indicators
     - 2
     - years,fv,return,mdd,v,ref,alpha,beta,sharp,info
     - | 对优化后的策略参数进行测试评价的评价指标。
       | 格式为逗号分隔的字符串，多个评价指标会以字典的形式输出，包含以下类型中的一种或多种
       | "years"       - total year
       | "fv"          - final values
       | "return"      - total return rate
       | "mdd"         - max draw down
       | "ref"         - reference data return
       | "alpha"       - alpha rate
       | "beta"        - beta rate
       | "sharp"       - sharp rate
       | "info"        - info rate
   * - indicator_plot_type
     - 2
     - histo
     - | 优化或测试结果评价指标的可视化图表类型:
       | 0  - errorbar 类型
       | 1  - scatter 类型
       | 2  - histo 类型
       | 3  - violin 类型
       | 4  - box 类型
   * - test_sub_periods
     - 3
     - 3
     - 仅当测试类型为"multiple"时有效。将测试区间切分为子区间的数量
   * - test_sub_prd_length
     - 3
     - 0.75
     - | 仅当测试类型为"multiple"时有效。每一个测试子区间长度占整个测试区间长度的比例
       | 例如，当测试区间长度为4年时，本参数0.75代表每个测试子区间长度为3年
   * - test_cycle_count
     - 3
     - 100
     - | 仅当测试类型为"montecarlo"时有效。生成的模拟测试数据的数量。
       | 默认情况下生成100组模拟价格数据，并进行100次策略回测并评价其统计结果
   * - optimize_target
     - 1
     - final_value
     - 策略的优化目标。即优化时以找到该指标最佳的策略为目标
   * - maximize_target
     - 1
     - True
     - 为True时寻找目标值最大的策略，为False时寻找目标值最低的策略
   * - opti_method
     - 1
     - 1
     - | 策略优化算法，可选值如下:
       | 0 - 网格法，按照一定间隔对整个向量空间进行网格搜索
       | 1 - 蒙特卡洛法，在向量空间中随机取出一定的点搜索最佳策略
       | 2 - 递进步长法，对向量空间进行多轮搜索，每一轮搜索结束后根据结果选择部分子
       |     空间，缩小步长进一步搜索
       | 3 - 遗传算法，模拟生物种群在环境压力下不断进化的方法寻找全局最优（尚未完成）
       | 4 - ML方法，基于机器学习的最佳策略搜索算法（尚未完成）
   * - opti_grid_size
     - 3
     - 1
     - 使用穷举法搜索最佳策略时有用，搜索步长
   * - | opti_sample_count
     - 3
     - 256
     - 使用蒙特卡洛法搜索最佳策略时有用，在向量空间中采样的数量
   * - opti_r_sample_count
     - 3
     - 16
     - 在使用递进步长法搜索最佳策略时有用，每一轮随机取样的数量
   * - opti_reduce_ratio
     - 3
     - 0.1
     - | 在使用递进步长法搜索最佳策略时有用，
       | 每一轮随机取样后择优留用的比例，同样也是子空间缩小的比例
   * - opti_max_rounds
     - 3
     - 5
     - 在使用递进步长法搜索最佳策略时有用，多轮搜索的最大轮数，轮数大于该值时停止搜索
   * - opti_min_volume
     - 3
     - 1000
     - 在使用递进步长法搜索最佳策略时有用，空间最小体积，当空间volume低于该值时停止搜索
   * - opti_population
     - 3
     - 1000.0
     - 在使用遗传算法搜索最佳策略时有用，种群的数量
   * - opti_output_count
     - 3
     - 30
     - 策略参数优化后输出的最优参数数量
