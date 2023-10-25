# qteasy -- a python-based fast quantitative investment utility module

![PyPI](https://img.shields.io/pypi/v/qteasy)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/qteasy)
[![Build Status](https://app.travis-ci.com/shepherdpp/qteasy.svg?branch=master)](https://app.travis-ci.com/shepherdpp/qteasy)
![GitHub](https://img.shields.io/github/license/shepherdpp/qteasy)
![GitHub repo size](https://img.shields.io/github/repo-size/shepherdpp/qteasy)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/shepherdpp/qteasy)
![GitHub top language](https://img.shields.io/github/languages/top/shepherdpp/qteasy)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/qteasy)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qteasy)
![GitHub branch checks state](https://img.shields.io/github/checks-status/shepherdpp/qteasy/master)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/shepherdpp/qteasy)
![GitHub issues](https://img.shields.io/github/issues/shepherdpp/qteasy)
![GitHub last commit](https://img.shields.io/github/last-commit/shepherdpp/qteasy)
![GitHub contributors](https://img.shields.io/github/contributors/shepherdpp/qteasy)
![PyPI - Downloads](https://img.shields.io/pypi/dm/qteasy)
![PyPI - Downloads](https://img.shields.io/pypi/dw/qteasy)
![GitHub Repo stars](https://img.shields.io/github/stars/shepherdpp/qteasy?style=social)
![GitHub forks](https://img.shields.io/github/forks/shepherdpp/qteasy?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/shepherdpp/qteasy?style=social)
![GitHub followers](https://img.shields.io/github/followers/shepherdpp?style=social)
![GitHub Sponsors](https://img.shields.io/github/sponsors/shepherdpp?style=social)


- [QTEASY简介](#基本介绍)
- [安装及依赖](#安装依赖包)
- [10分钟了解Qteasy的功能](#10分钟了解qteasy的功能)
  - [初始配置——本地数据源](#配置本地数据源)
  - [下载股票价格并可视化](#下载股票价格数据并将其可视化)
  - [创建投资策略](#创建一个投资策略)
  - [投资策略的回测和评价](#回测并评价交易策略的性能表现)
  - [投资策略的实盘运行](#投资策略的实盘运行)
  - [投资策略的优化](#回测并优化交易策略)
- [更详细的使用方法请参见教程](#QTEASY使用教程)

## Introduction
- Author: **Jackie PENG**
- email: *jackie_pengzhao@163.com*
- Created: 2019, July, 16
- Latest Version: `0.0.1.dev7`

This project is aiming at a fast quantitative investment package for python, with following functions:


1. Historical stock data acquiring and bundling, visualization 
2. Investment strategy creation, backtesting, assessment and optimization 
3. Live stock trading: trading operation submission, withdrawal, status checking and feedback reporting 

The target of this module is to provide effective vectorized backtesting and assessment of investment 
strategies, with highly versertility and flexibility

## Installation and dependencies

### Install `qteay` from PyPI

```bash
pip install qteasy
```
### Install dependencies

This project requires and depends on following packages:
- *`pandas` version >= 0.25.1, <1.0.0*    `pip install pandas` / `conda install pandas`
- *`numpy` version >= 1.18.1*    `pip install numpy` / `conda install numpy`
- *`numba` version >= 0.47*    `pip install numba` / `conda install numba`
- *`TA-lib` version >= 0.4.18*    `pip install ta-lib` / `conda install -c conda-forge ta-lib`
- *`tushare` version >= 1.2.89*    `pip install tushare`
- *`mplfinance` version >= 0.11*    `pip install mplfinance` / `conda install -c conda-forge mplfinance`

A local datasource should be setup for `qteasy` to work properly. a series of .csv files will be used to store 
financial data in default case. Other types of datasource can be used, such as MySQL database, but other dependencies
should be installed. find more details in the tutorial.

##  Gets to know qteasy in 10 Min

### Import the module 


```python
import qteasy as qt
```
### Configure local data source and Tushare token

`qteasy` is not fully functional without variant types of financial data, which should be stored locally in a datasource.
Huge amounts of financial data can be readily downloaded with the help of `tushare`, a financial data package for python.
However, a Tushare API token is required to access the data. Please refer to [Tushare API token](https://tushare.pro/document/2) for details.

Users can configure the local data source and Tushare token in the configuration file `qteasy.cfg` under `QT_ROOT_PATH/qteasy/` path:

```
# qteasy configuration file
# following configurations will be loaded when initialize qteasy

# example:
# local_data_source = database
```
#### configure tushare token

add your `tushare` API token to the configuration file as follows:

``` commandline
tushare_token = <Your tushare API Token> 
```
#### Configure local datasource -- use MySQL database as an example

`qteasy` can use local `.csv` files as default data source, no special configuration is needed in this case.
Add following configurations to the configuration file to use `MySQL` database as local data source:


```bash
local_data_source = database  
local_db_host = <host name>
local_db_port = <port number>
local_db_user = <user name>
local_db_password = <password>
local_db_name = <database name>
```

Save and close the configuration file, then import `qteasy` again to activate new configurations.


### Download historical financial data 

Download historical financial data with `qt.refill_data_source()` function. 
The following code will download all stock and index daily price data from 2021 to 2022, and all stock and fund basic information data.
depending on connection, it may take about 10 minutes to download all data. The data will take about 200MB disk space if stored as csv files.


```python
qt.refill_data_source(
        tables=['stock_daily',   # daily price of stocks
                'index_daily',   # daily price of indexes
                'basics'],       # basic information of stocks and funds
        start_date='20210101',  # start date of data to download
        end_date='20221231',  
)
```
Downloaded data can be retrieved with `qt.get_history_data()` function. 
Data of multiple stocks will be stored in a `dict` object.

```python
qt.get_history_data(htypes='open, high, low, close', 
                    shares='000001.SZ, 000300.SH',
                    start='20210101',
                    end='20210115')
```
Above code returns a `dict` containing stock symbols as keys and Dataframe of prices as dict values:
```
{'000001.SZ':
              open   high    low  close
 2021-01-04  19.10  19.10  18.44  18.60
 2021-01-05  18.40  18.48  17.80  18.17
 2021-01-06  18.08  19.56  18.00  19.56
 ... 
 2021-01-13  21.00  21.01  20.40  20.70
 2021-01-14  20.68  20.89  19.95  20.17
 2021-01-15  21.00  21.95  20.82  21.00,
 
 '000300.SH':
                  open       high        low      close
 2021-01-04  5212.9313  5284.4343  5190.9372  5267.7181
 2021-01-05  5245.8355  5368.5049  5234.3775  5368.5049
 2021-01-06  5386.5144  5433.4694  5341.4304  5417.6677
 ...
 2021-01-13  5609.2637  5644.7195  5535.1435  5577.9711
 2021-01-14  5556.2125  5568.0179  5458.6818  5470.4563
 2021-01-15  5471.3910  5500.6348  5390.2737  5458.0812}
```
Apart from prices, `qteasy` can also download and manage a large amount of financial data, including financial statements, technical indicators, and basic information. For details, please refer to
[QTEASY tutorial: download and manage financial data](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2002%20-%20金融数据获取及管理.md)

As a shortcut, `qteasy` provides a `qt.candle()` function to plot candlestick charts of stock prices already downloaded

```python
data = qt.candle('000300.SH', start='2021-06-01', end='2021-8-01', asset_type='IDX')
```

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_5_2.png)
    
`qteasy`的K线图函数`candle`支持通过六位数股票/指数代码查询准确的证券代码，也支持通过股票、指数名称显示K线图
`qt.candle()` supports plotting:
- Candle stick chart of stocks, funds and futures,
- in adjusted prices and unadjusted prices,
- in different frequencies like minute, week or month,
- together with different moving averages and technical indicators like MACD/KDJ,

More detailed intro can be found in tutorial. Here are some examples:

(Please make sure you have downloaded the data with `qt.refill_data_source()` first)


```python
# Hourly candle stick chart of fund
qt.candle('159601', start = '20220121', freq='h')
# Daily price K-line chart of HS300 index
qt.candle('000300', start = '20200121')
# Adjusted 30-min K-line chart of stocks
qt.candle('中国电信', start = '20211021', freq='30min', adj='b')
# K-line chart of futures with specified moving averages (9, 12, 26 days)
qt.candle('沪铜主力', start = '20211021', mav=[9, 12, 26])
# Net value chart of funds, adjusted net value, no moving average
qt.candle('000001.OF', start='20200101', asset_type='FD', adj='b', mav=[])
```

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_3_1.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_7_2.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_8_3.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_3_4.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_3_5.png)
    


生成的K线图可以是一个交互式动态K线图（请注意，K线图基于`matplotlib`绘制，在使用不同的终端时，显示功能有所区别，某些终端并不支持
动态图表，详情请参阅 [matplotlib文档](https://matplotlib.org/stable/users/explain/backends.html)


在使用动态K线图时，用户可以用鼠标和键盘控制K线图的显示范围：

- 鼠标在图表上左右拖动：可以移动K线图显示更早或更晚的K线
- 鼠标滚轮在图表上滚动，可以缩小或放大K线图的显示范围
- 通过键盘左右方向键，可以移动K线图的显示范围显示更早或更晚的K线
- 通过键盘上下键，可以缩小或放大K线图的显示范围
- 在K线图上双击鼠标，可以切换不同的均线类型
- 在K线图的指标区域双击，可以切换不同的指标类型：MACD，RSI，DEMA

![gif](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_dyna_plot.gif)

关于`DataSource`对象的更多详细介绍，请参见[qteasy教程](https://github.com/shepherdpp/qteasy/tutorials)


###  创建一个投资策略 Create an investment strategy

`qteasy`中的所有交易策略都是由`qteast.Operator`（交易员）对象来实现回测和运行的，`Operator`对象是一个策略容器，一个交易员可以同时
管理多个不同的交易策略。

`queasy`提供了两种方式创建交易策略，详细的说明请参见使用教程：

- **使用内置交易策略组合**
- **通过策略类自行创建策略**

#### 生成一个DMA均线择时交易策略
在这里，我们将使用一个内置的`DMA`均线择时策略来生成一个最简单的大盘择时交易系统。所有内置交易策略的清单和详细说明请参见文档。

创建`Operator`对象时传入参数：`strategies='DMA'`，可以新建一个`DMA`双均线择时交易策略。
创建好`Operator`对象后，可以用`op.info()`来查看它的信息。

```python
import qteasy as qt

op = qt.Operator(strategies='dma')
op.info()
```
现在可以看到`op`中有一个交易策略，ID是`dma`，我们在`Operator`层面设置或修改策略的参数
时，都需要引用这个`ID`。

`DMA`是一个内置的均线择时策略，它通过计算股票每日收盘价的快、慢两根移动均线的差值`DMA`与其移动平均值`AMA`之间的交叉情况来确定多空或买卖点。：

使用qt.built_ins()函数可以查看DMA策略的详情，例如：
```python
qt.built_ins('dma')
```
得到：

```
 DMA择时策略

    策略参数：
        s, int, 短均线周期
        l, int, 长均线周期
        d, int, DMA周期
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        在下面情况下产生买入信号：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线后，输出为1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线后，输出为0
        3， DMA与股价发生背离时的交叉信号，可信度较高

    策略属性缺省值：
    默认参数：(12, 26, 9)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(10, 250), (10, 250), (8, 250)]
    策略不支持参考数据，不支持交易数据
```
在默认情况下，策略由三个**可调参数**：`(12,26,9)`, 但我们可以给出任意大于2小于250的三个整数作为策略的参数，以适应不同交易活跃度的股票、或者适应
不同的策略运行周期。


### 回测并评价交易策略的性能表现
queasy可以使用历史数据回测策略表现并输出图表如下：
![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_14_3.png)

使用默认参数回测刚才建立的DMA策略在历史数据上的表现，可以使用`op.run()`。

```python
res = op.run(
        mode=1,                         # 历史回测模式
        asset_pool='000300.SH',         # 投资资产池
        asset_type='IDX',               # 投资资产类型
        invest_cash_amounts=[100000],   # 投资资金
        invest_start='20220501',        # 投资回测开始日期
        invest_end='20221231',          # 投资回测结束日期
        cost_rate_buy=0.0003,           # 买入费率
        cost_rate_sell=0.0001,          # 卖出费率
        visual=True,                    # 打印可视化回测图表
        trade_log=True                  # 打印交易日志
)
```
输出结果如下：
```
     ====================================
     |                                  |
     |       BACK TESTING RESULT        |
     |                                  |
     ====================================

qteasy running mode: 1 - History back testing
time consumption for operate signal creation: 4.4 ms
time consumption for operation back looping:  82.5 ms

investment starts on      2022-05-05 00:00:00
ends on                   2022-12-30 00:00:00
Total looped periods:     0.7 years.

-------------operation summary:------------
Only non-empty shares are displayed, call 
"loop_result["oper_count"]" for complete operation summary

          Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
000300.SH    6        6      12   56.4%      0.0%     43.6%   

Total operation fee:     ¥      257.15
total investment amount: ¥  100,000.00
final value:              ¥  105,773.09
Total return:                     5.77% 
Avg Yearly return:                8.95%
Skewness:                          0.58
Kurtosis:                          3.54
Benchmark return:                -3.46% 
Benchmark Yearly return:         -5.23%

------strategy loop_results indicators------ 
alpha:                            0.142
Beta:                             1.003
Sharp ratio:                      0.637
Info ratio:                       0.132
250 day volatility:               0.138
Max drawdown:                    11.92% 
    peak / valley:        2022-08-17 / 2022-10-31
    recovered on:         Not recovered!

===========END OF REPORT=============
```
![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_21_1.png)

### 交易策略的参数调优

交易策略的表现与参数有关，如果输入不同的参数，策略回报相差会非常大。`qteasy`可以用多种不同的优化算法，帮助搜索最优的策略参数，

要使用策略优化功能，需要设置交易策略的优化标记`opt_tag=1`，并配置环境变量`mode=2`即可:

```python
op.set_parameter('dma', opt_tag=1)
res = op.run(mode=2,                    # 优化模式
             opti_start='20220501',     # 优化区间开始日期
             opti_end='20221231',       # 优化区间结束日期
             test_start='20220501',     # 测试区间开始日期
             test_end='20221231',       # 测试区间结束日期
             opti_sample_count=1000,    # 优化样本数量
             visual=True,               # 打印优化结果图表
             parallel=False)            # 不使用并行计算
```

`qteasy`将在同一段历史数据（优化区间）上反复回测，找到结果最好的30组参数，并把这30组参数在另一段历史数据（测试区间）上进行独立测试，并显
示独立测试的结果：
```commandline
==================================== 
|                                  |
|       OPTIMIZATION RESULT        |
|                                  |
====================================

qteasy running mode: 2 - Strategy Parameter Optimization

... # 省略部分输出

# 以下是30组优化的策略参数及其结果（部分结果省略）
    Strategy items Sell-outs Buy-ins ttl-fee     FV      ROI  Benchmark rtn MDD 
0     (35, 69, 60)     1.0      2.0    71.45 106,828.20  6.8%     -3.5%     9.5%
1   (124, 104, 18)     3.0      2.0   124.86 106,900.59  6.9%     -3.5%     7.4%
2   (126, 120, 56)     1.0      1.0    72.38 107,465.86  7.5%     -3.5%     7.5%
...
27   (103, 84, 70)     1.0      1.0    74.84 114,731.44 14.7%     -3.5%     8.8%
28  (143, 103, 49)     1.0      1.0    74.33 116,453.26 16.5%     -3.5%     4.3%
29   (129, 92, 56)     1.0      1.0    74.55 118,811.58 18.8%     -3.5%     4.3%

===========END OF REPORT=============
```

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_24_1.png)   
将优化后的参数应用到策略中，并再次回测，可以看到结果明显提升：

```python
op.set_parameter('dma', pars=(143, 99, 32))
res = op.run(
        mode=1,                         # 历史回测模式
        asset_pool='000300.SH',         # 投资资产池
        asset_type='IDX',               # 投资资产类型
        invest_cash_amounts=[100000],   # 投资资金
        invest_start='20220501',        # 投资回测开始日期
        invest_end='20221231',          # 投资回测结束日期
        cost_rate_buy=0.0003,           # 买入费率
        cost_rate_sell=0.0001,          # 卖出费率
        visual=True,                    # 打印可视化回测图表
        trade_log=True                  # 打印交易日志
```
结果如下：

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_26_1.png)   


关于策略优化结果的更多解读、以及更多优化参数的介绍，请参见详细文档

### 部署并开始交易策略的实盘运行

`qteasy`提供了在命令行环境中运行的一个简单实盘交易程序，在配置好Operator对象并设置好策略后，自动定期运行、下载实时数据并根据策略结果生成交易指令，模拟交易过程并记录交易结果。

在`Operator`中设置好交易策略，并配置好交易参数后，可以直接启动实盘交易：

```python
import qteasy as qt

# 创建一个交易策略alpha
alpha = qt.get_built_in_strategy('ndayrate')  # 创建一个N日股价涨幅交易策略

# 设置策略的运行参数
alpha.strategy_run_freq = 'd'  # 每日运行
alpha.data_freq = 'd' # 策略使用日频数据
alpha.window_length = 20  # 数据窗口长度
alpha.sort_ascending = False  # 优先选择涨幅最大的股票
alpha.condition = 'greater'  # 筛选出涨幅大于某一个值的股票
alpha.ubound = 0.005  # 筛选出涨幅大于0.5%的股票
alpha.sel_count = 7  # 每次选出7支股票

# 创建一个交易员对象，运行alpha策略
op = qt.Operator(alpha, signal_type='PT', op_type='step')

# 设置策略运行参数
# 交易股票池包括所有的银行股和家用电器股
asset_pool = qt.filter_stock_codes(industry='银行, 家用电器', exchange='SSE, SZSE')

qt.configure(
        mode=0,  # 交易模式为实盘运行
        asset_type='E',  # 交易的标的类型为股票
        asset_pool=asset_pool,  # 交易股票池为所有银行股和家用电器股
        trade_batch_size=100,  # 交易批量为100股的整数倍
        sell_batch_size=1,  # 卖出数量为1股的整数倍
        live_trade_account_id=1,  # 实盘交易账户ID
        live_trade_account='user name',  # 实盘交易用户名
)

qt.run(op)
```
此时`qteasy`会启动一个`Trader Shell`命令行界面，同时交易策略会自动定时运行，运行的参数随`QT_CONFIG`而定。启动TraderShell后，所有交易相关的重要信息都会显示在console中：

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_27_1.png)   

此时控制台上会显示当前交易执行状态：
- 当前日期、时间、运行状态
- 产生的交易信号和交易订单
- 交易订单的成交情况
- 账户资金变动情况
- 账户持仓变动情况
- 开盘和收盘时间预告等

在`TraderShell`运行过程中可以随时按`Ctrl+C`进入Shell选单：
```commandline
Current mode interrupted, Input 1 or 2 or 3 for below options: 
[1], Enter command mode; 
[2], Enter dashboard mode. 
[3], Exit and stop the trader; 
please input your choice: 
```

此时按1可以进入Interactive模式（交互模式）。在交互模式下，用户可以在(QTEASY)命令行提示符后输入
命令来控制交易策略的运行：

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/img/output_28_1.png)   

在命令行模式下可以与`TraderShell`实现交互，操作当前账户，查询交易历史、修改状态等：

- `pause` / `resume`: 暂停/重新启动交易策略
- `change`: 修改当前持仓和现金余额
- `positions`: 查看当前持仓
- `orders`: 查看当前订单
- `history`: 查看历史交易记录
- `exit`: 退出TraderShell
- ... 更多`TraderShell`命令参见`QTEASY`文档

## QTEASY 使用教程

关于`QTEASY`系统的更多详细解释和使用方法，请参阅以下使用教程：

- [01: 系统基础配置及初始化](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2001%20-%20系统基础配置.md)
- [02: 金融数据下载及管理](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2002%20-%20金融数据获取及管理.md)
- [03: 交易策略及回测基本操作](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2003%20-%20交易策略及回测基本操作.md)
- [04: 使用内置交易策略](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2004%20-%20使用内置交易策略.md)
- [05: 创建自定义交易策略(未完待续)](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2005%20-%20创建自定义交易策略.md)
- [06: 交易策略的参数优化(未完待续)](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2006%20-%20交易策略的优化.md)
- [07: 交易策略的部署和运行(未完待续)](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2007%20-%20交易策略的部署及运行.md)
- [08: 历史数据的操作和分析(未完待续)](https://github.com/shepherdpp/qteasy/blob/master/tutorials/Tutorial%2008%20-%20历史数据的操作和分析.md)
