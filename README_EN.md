# qteasy -- a python-based fast quantitative investment utility module

![PyPI](https://img.shields.io/pypi/v/qteasy)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/qteasy)
[![Build Status](https://app.travis-ci.com/shepherdpp/qteasy.svg?branch=master)](https://app.travis-ci.com/shepherdpp/qteasy)
[![Documentation Status](https://readthedocs.org/projects/qteasy/badge/?version=latest)](https://qteasy.readthedocs.io/zh/latest/?badge=latest)
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


- [Introduction](#Introduction)
- [QTEASY Documentations](#QTEASY-Documentations)
- [Installation and dependencies](#installation-and-dependencies)
  - [Install `qteasy` from pypi](#install-qteay-from-pypi)
  - [Install dependencies](#install-dependencies)
- [Gets to know `qteasy` in 10 min](#gets-to-know-qteasy-in-10-min)
  - [Configure `qteasy` and data source](#configure-local-data-source-and-tushare-token)
  - [Acquire and visualize financial data](#download-historical-financial-data)
  - [Create a strategy](#create-an-investment-strategy)
  - [Back test and assess Strategy](#backtest-strategy-with-history-data-and-evaluate-its-performance)
  - [Deploy Strategy](#deploy-the-strategy-and-start-live-trading)
  - [Optimizing Strategy](#optimize-adjustable-parameters-of-a-strategy)

## Introduction
- Author: **Jackie PENG**
- email: *jackie_pengzhao@163.com*
- Created: 2019, July, 16
- Latest Version: `1.0.9`
- License: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication

QTEASY is a fast quantitative investment package created for traders, with following features:

1. Acquire, clean, organize, visualize, store and query financial data, including stock price, financial statements, technical indicators, and basic information of stocks and funds. Downloaded data can be stored locally in forms of csv files or MySQL database. Data can be acquired from Tushare, eastMoney, etc.
2. Create, backtest and assess investment strategies, and optimize adjustable parameters of strategies with a series of optimization algorithms.
3. Deploy strategies and start live trading with real-time data, and record trading logs, account positions and funds.

Following functions are in development plan:
1. *Provide common financial statistical analysis tools and integrate them into the HistoryPanel object (in development)*
2. *Connect with automated trading system and realize automated trading (in development)*

The target of this module is to provide effective vectorized backtesting and assessment of investment 
strategies, with highly versertility and flexibility


## QTEASY Documentations

You can find more about qteasy in the `QTEASY` [documents](https://qteasy.readthedocs.io):


## Installation and dependencies

### Install `qteay` from PyPI

```bash
$ pip install qteasy
```

### python version
- *`python` version >= 3.6* 

### Install dependencies

This project requires and depends on following packages:
- *`pandas` version >= 1.1.0*    `pip install pandas` / `conda install pandas`
- *`numpy` version >= 1.18.1*    `pip install numpy` / `conda install numpy`
- *`numba` version >= 0.47*    `pip install numba` / `conda install numba`
- *`tushare` version >= 1.2.89*    `pip install tushare`
- *`mplfinance` version >= 0.11*    `pip install mplfinance` / `conda install -c conda-forge mplfinance`
- *`rich` version >= 10.0.0*    `pip install rich` / `conda install -c conda-forge rich`


- *`TA-lib` version >= 0.4.18*    the TA-Lib will have to be installed manually, please refer to [TA-Lib installation](https://qteasy.readthedocs.io/zh/latest/faq.html) for details.

A local datasource should be setup for `qteasy` to work properly. a series of .csv files will be used to store 
financial data in default case. Other types of datasource can be used, such as MySQL database, but other dependencies
should be installed. find more details in the tutorial.

##  Gets to know qteasy in 10 Min

### Import the module 


```python
import qteasy as qt
print(qt.__version__)
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
[QTEASY documents](https://qteasy.readthedocs.io)

As a shortcut, `qteasy` provides a `qt.candle()` function to plot candlestick charts of stock prices already downloaded

```python
data = qt.candle('000300.SH', start='2021-06-01', end='2021-8-01', asset_type='IDX')
```

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_5_2.png)
    
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

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_3_1.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_7_2.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_8_3.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_3_4.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_3_5.png)
    

The candlestick chart generated by `qt.candle()` is an interactive dynamic chart (please note that the candlestick chart is based on `matplotlib`, and the display function is different when using different terminals. Some terminals do not support dynamic charts. For details, please refer to [matplotlib documentation](https://matplotlib.org/stable/users/explain/backends.html)

With the dynamic candlestick chart, users can control the display range of the K-line chart with the mouse and keyboard to:

- view earlier and later prices by dragging the mouse， and
- zoom in or out by scrolling the mouse wheel， and
- view earlier and later prices by pressing left and right arrow keys， and
- zoom in or out by pressing up and down arrow keys， and
- view different moving averages by double clicking the mouse on the chart， and
- view different technical indicators by double clicking the mouse on the indicator area

![gif](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_dyna_plot.gif)

Find more detailed introduction to DataSource objects in [QTEASY documents](https://qteasy.readthedocs.io)


###  Create an investment strategy

In `qteasy`, all trade strategies are implemented by an `Operator` object, which is a container of strategies. An operator can manage multiple strategies at the same time and triger one or more strategies at the right timing.

A `qteasy` trade strategy can be created in two ways, please refer to the tutorial for detailed instructions:

- **Combined with built-in strategies**, or 
- **Constructed with `Strategy` class**

#### Create a DMA strategy

To create an Operator with a DMA strategy, pass `strategies='DMA'` to the `Operator` constructor, a `DMA` trade strategy will be created because 'DMA' strategy is a built-in strategy.

You may view the details of the DMA strategy with `op.info()` method:

```python
op = qt.Operator(strategies='dma')
op.info()
```
```bash
            -----------------------Operator Information-----------------------
Strategies:  1 Strategies
Run Mode:    batch - All history operation signals are generated before back testing
Signal Type: pt - Position Target, signal represents position holdings in percentage of total value

            ------------------------Strategy blenders-------------------------
for strategy running timing - close:
no blender

            ----------------------------Strategies----------------------------
stg_id    name                  run timing   data window       data types             parameters     
____________________________________________________________________________________________________
dma       DMA                  days @ close  270 x days        ['close']            (12, 26, 9)     
====================================================================================================
```
Now a strategy is added to the operator with ID 'dma', with which we can set or modify parameters of the strategy.

'DMA' is a built-in timing strategy that generates buy/sell signals based on the difference between the fast and slow moving averages of the stock price. 

Detailed info of this strategy can be print out with `op.info()` method:

```python
qt.built_ins('dma')
```
following info will be printed:

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
By default, the strategy uses three **adjustable parameters**: `(12,26,9)`, but we can give any three integers greater than 2 and less than 250 as the parameters of the strategy to adapt to stocks with different trading activity or to adapt to different strategy running cycles.


### Backtest strategy with history data and evaluate its performance

with `qteasy`, one can easily backtest a strategy with historical data and evaluate its performance.

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_14_3.png)

Use `op.run()` to run the strategy with historical data, and the result will be returned as a `dict` object:

```python
res = op.run(
        mode=1,                         # run in backtest mode
        asset_pool='000300.SH',         # the list symbols in trading pool 
        asset_type='IDX',               # the type of assets to be traded
        invest_cash_amounts=[100000],   # initial investment cash amount
        invest_start='20220501',        # start date of backtest
        invest_end='20221231',          # end date of backtest
        cost_rate_buy=0.0003,           # trade cost rate for buying
        cost_rate_sell=0.0001,          # trade cost rate for selling
        visual=True,                    # print visualized backtest result
        trade_log=True                  # save trade log
)
```
Here's printed trade result:
```commandline
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
The backtest result is also visualized in a chart as well:

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_21_1.png)

### Optimize adjustable parameters of a strategy

The performance of a strategy highly depends on its adjustable parameters, and often varies a lot with different parameters. `qteasy` provides a series of optimization algorithms to help search for the best parameters of a strategy.

To run qteasy in optimization mode, set optimization tag of the strategy: `opt_tag=1`, and set environment variable `mode=2`:


```python
op.set_parameter('dma', opt_tag=1)
res = op.run(mode=2,                    # run in optimization mode
             opti_start='20220501',     # start date of optimization period
             opti_end='20221231',       # end date of optimization period
             test_start='20220501',     # start date of test period
             test_end='20221231',       # end date of test period
             opti_sample_count=1000,    # sample count of optimization
             visual=True,               # print visualized backtest result
             parallel=True)            # run in parallel mode
```

`qteasy` tries to find the 30 sets of best-performing parameters of a strategy on the optimization period, and perform independent backtest on the test period. The result of the optimization will be printed as follows:

```commandline
==================================== 
|                                  |
|       OPTIMIZATION RESULT        |
|                                  |
====================================

qteasy running mode: 2 - Strategy Parameter Optimization

... # ommited for brevity

# 30 sets of optimized parameters and their results (partially omitted for brevity)
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

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_24_1.png)
Run backtest again with the optimized parameters, and the result will be improved significantly:

```python
op.set_parameter('dma', pars=(143, 99, 32))
res = op.run(
        mode=1,                         # run in backtest mode
        asset_pool='000300.SH',         # the list symbols in trading pool
        asset_type='IDX',               # the type of assets to be traded
        invest_cash_amounts=[100000],   # initial investment cash amount
        invest_start='20220501',        # start date of backtest
        invest_end='20221231',          # end date of backtest
        cost_rate_buy=0.0003,           # trade cost rate for buying
        cost_rate_sell=0.0001,          # trade cost rate for selling
        visual=True,                    # print visualized backtest result
        trade_log=True)                 # save trade log
```

here's result：

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_26_1.png)   

For more detailed info about the optimization result, please refer to the tutorial.

### Deploy the strategy and start live trading

`qteasy` provides a simple live trading program that runs in command line environment. After configuring the `Operator` object and setting the strategy, it runs automatically, downloads real-time data, generates trading instructions according to the strategy results, simulate the trading process and record the trading results.

Live trade can be started when strategy is setup with its parameters and configured with `Operator` object. 

```python
import qteasy as qt

# create trade strategy alpha
alpha = qt.get_built_in_strategy('ndayrate')  # create a N-day price change trade strategy 

# set strategy parameters
alpha.strategy_run_freq = 'd'  # strategy runs daily
alpha.data_freq = 'd' # strategy uses daily data
alpha.window_length = 20  # length of data window
alpha.sort_ascending = False  # select stocks with largest price change
alpha.condition = 'greater'  # filter stocks with price change greater than:
alpha.ubound = 0.005  # 0.5%.
alpha.sel_count = 7  # select at most 7 stocks each time 

# create an operator object containing alpha strategy
op = qt.Operator(alpha, signal_type='PT', op_type='step')

# set up strategy running parameters
# asset pool contains all bank stocks and home appliance stocks
asset_pool = qt.filter_stock_codes(industry='银行, 家用电器', exchange='SSE, SZSE')

qt.configure(
        mode=0,  # run in live trade mode
        asset_type='E',  # asset type is stock
        asset_pool=asset_pool,  # stock pool contains all bank stocks and home appliance stocks
        trade_batch_size=100,  # trade batch size is 100
        sell_batch_size=1,  # sell batch size is 1
        live_trade_account_id=1,  # live trade account ID
        live_trade_account='user name',  # live trade account user name
)

qt.run(op)
```
A `TraderShell` command line interface will be started, automatically running strategy at the right time. The parameters 
of the strategy are determined by the `QT_CONFIG` environment variable. After the `TraderShell` command line interface 
is started, all important information related to the transaction will be displayed in the console:

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_27_1.png)   

In the `TraderShell`, following key information will be displayed on the console:
- current date, time and running status, 
- the trading signals and orders generated by the strategy, 
- the execution status of the trading orders,
- the change of account funds, and,
- the change of account positions.

You can press `Ctrl+C` to view Shell menu at any time during the running of `TraderShell`:
```commandline
Current mode interrupted, Input 1 or 2 or 3 for below options: 
[1], Enter command mode; 
[2], Enter dashboard mode. 
[3], Exit and stop the trader; 
please input your choice: 
```
then press 1 to enter interactive mode, in which user command is taken and executed:

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/master/docs/source/img/output_28_1.png)   

Users interact with, control and modify behavior of the live trading by inputting commands. The following commands are supported:

- `pause` / `resume`: pause or resume live trading
- `strategies`: view current strategies and parameters
- `change`: change current position and cash amount
- `positions`: view current positions of holdings
- `orders`: view trade orders
- `history`: view trade history
- `exit`: exit TraderShell
- ... more commands please refer to `QTEASY` documentation
