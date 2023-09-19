# `qteasy` -- 一个基于Python的高效量化投资工具包

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

## QTEASY简介

- Author: **Jackie PENG**
- email: *jackie_pengzhao@163.com*
- Created: 2019, July, 16
- Latest Version: `1.0.0`

本项目旨在开发一套基于python的本地运行的量化交易策略回测和开发工具，包含以下基本功能

1. 金融历史数据的获取、清洗、整理、可视化、本地存储查询及应用，并*提供一些金融统计数据分析工具（开发中）*
2. 投资交易策略的创建、回测、性能评价，并且通过定义策略的可调参数，提供多种优化算法实现交易策略的参数调优
3. 交易策略的部署、实盘运行，未来还将实现*与自动化交易系统连接、实现自动化交易(开发中)*


开发本模块的目标是为量化交易人员提供一套量化交易策略开发框架，提供了金融数据下载和分析，交易策略快速回测，策略可调参数的寻优以及交易策略实盘运行等功能。


## 安装及依赖

### `qteasy`的安装

`python -m pip install qteasy`

### 安装依赖包

这个项目依赖以下python package，有些安装包可能不能在安装`qteasy`的时候自动安装，此时可以手动安装:
- *`pandas` version >= 0.25.1, <1.0.0*    `pip install pandas` / `conda install pandas`
- *`numpy` version >= 1.18.1*    `pip install numpy` / `conda install numpy`
- *`numba` version >= 0.47*    `pip install numba` / `conda install numba`
- *`TA-lib` version == 0.4.18*    `pip install ta-lib==0.4.18`
- *`tushare` version >= 1.2.89*    `pip install tushare`
- *`mplfinance` version >= 0.11*    `pip install mplfinance` / `conda install -c conda-forge mplfinance`

## 可选依赖包
使用`qteasy`需要设置本地数据源，默认使用csv文件作为本地数据源，如果选用其他数据源，需要安装以下可选依赖包
### 如果使用mysql数据库作为本地数据源
- *`pymysql` version >= 1.0.0*    `pip install pymysql` / `conda install -c anaconda pymysql`
- *`sqlalchemy` version >= 1.4.18, <=1.4.23*   `pip install sqlalchemy` / `conda install sqlalchemy`

### 如果使用hdf文件作为本地数据源 
- *`pytables` version >= 3.6.1*   `conda install -c conda-forge pytables`

### 如果使用feather文件作为本地数据源
- *`pyarrow` version >= 3*   `pip install pyarrow` / `conda install -c conda-forge pyarrow`


##  10分钟了解qteasy的功能

基本的模块导入方法如下

```python
import qteasy as qt
```

### 配置本地数据源

为了使用`qteasy`，需要大量的金融历史数据，所有的历史数据都必须首先保存在本地，如果本地没有历史数据，那么`qteasy`的许多功能就无法执行。

`qteasy`可以通过`tushare`金融数据包来获取大量的金融数据，用户需要自行申请API Token，获取相应的权限和积分（详情参考：https://tushare.pro/document/2）

因此，在使用`qteasy`之前需要对本地数据源和`tushare`进行必要的配置，初始配置是通过一个文件`qteasy.cfg`来实现的。第一次导入`qteasy`时，
`qteasy`
会在QT_ROOT_PATH/qteasy/下创建一个空白的配置文件，用TextEdit或Notepad打开文件可以看到下面内容：

```
# qteasy configuration file
# following configurations will be loaded when initialize qteasy

# example:
# local_data_source = database

```

> - 使用`qt.QT_ROOT_PATH`可以查看qteasy的根目录
> - `tushare` 的`API token`可以到[tushare pro主页](https://tushare.pro)免费申请


在文件中直接添加下面的配置后保存即可：

```
# qteasy configuration file
# following configurations will be loaded when initialize qteasy

# example:
# local_data_source = database

tushare_token = <你的tushare API Token> 

# 如果设置使用mysql数据库作为本地数据源，需要设置：
local_data_source = database  
# 同时设置mysql数据库的连接信息
local_db_host = <host name>
local_db_port = <port number>
local_db_user = <user name>
local_db_password = <password>
local_db_name = <database name>

# 如果使用csv文件作为本地数据源：
local_data_source = file
# 需要设置文件类型和存储路径
local_data_file_type = csv  # 或者hdf/fth分别代表hdf5文件或feather文件
local_data_file_path = data/  # 或者其他指定的文件存储目录

# 如果要使用tests目录下的测试数据，需要设置：
test_db_host = <host name>
test_db_port = <port number>
test_db_user = <user name>
test_db_password = <password>
test_db_name = test_db <或其他用于测试的临时数据库>

```
根据你选择的本地数据源类型，可能需要安装对应的依赖包，参见[安装及依赖](#安装依赖包)

如果日常使用的数据量大，建议设置`data_source_type = database`，使用数据库保存本地数据。不包括分钟数据时，所有数据将占用大约10G的磁盘空
间， 分钟级别数据将占用350GB甚至更多的磁盘空间。

关闭并保存好配置文件后，重新导入`qteasy`，就完成了数据源的配置，可以开始下载数据到本地了。

### 下载股票价格数据并将其可视化 

要下载数据，使用`qt.refill_data_source()`函数。下面的代码下载一年内所有股票的日K线数据：

```python
import qteasy as qt
qt.refill_data_source(tables='stock_daily', start_date='20210101', end_date='20220101')
```

> `qt.refill_data_source()`的`tables`参数指定需要补充的数据表；
> 除了直接给出表名称以外，还可以通过表类型同时下载多个数据表的数据：
> 
> - `cal`     : 交易日历表，各个交易所的交易日历
> - `basics`  : 所有的基础信息表，包括股票、基金、指数、期货、期权的基本信息表
> - `adj`     : 所有的复权因子表，包括股票、基金的复权因子，用于生成复权价格
> - `data`    : 所有的历史数据表，包括股票、基金、指数、期货、期权的日K线数据以及周、月K线数据
> - `events`  : 所有的历史事件表，包括股票更名、更换基金经理、基金份额变动等数据
> - `report`  : 财务报表，包括财务指标、三大财务报表、财务快报、月报、季报以及年报
> - `comp`    : 指数成分表，包括各个指数的成份股及其百分比
> - `all`     : 所有的数据表，以上所有数据表，由于数据量大，建议分批下载


数据下载到本地后，可以使用`qt.get_history_data()`来获取数据，如果同时获取多个股票的历史数据，每个股票的历史数据会被分别保存到一个`dict`中。

```python
import qteasy as qt

qt.get_history_data(htypes='open, high, low, close', 
                    shares='000001.SZ, 000005.SZ',
                    start='20210101',
                    end='20210201')
```
运行上述代码会得到一个`Dict`对象，包含两个股票"000001.SZ"以及"000005.SZ"的K线数据（数据存储为`DataFrame`）：
```
{'000001.SZ':
              open   high    low  close
 2021-01-04  19.10  19.10  18.44  18.60
 2021-01-05  18.40  18.48  17.80  18.17
 2021-01-06  18.08  19.56  18.00  19.56
 ... 
 2021-01-28  22.78  23.18  22.45  22.81
 2021-01-29  22.81  23.54  22.71  23.09
 2021-02-01  23.00  24.99  22.70  24.55,
 
 '000005.SZ':
             open  high   low  close
 2021-01-04  2.53  2.53  2.51   2.52
 2021-01-05  2.52  2.52  2.46   2.47
 2021-01-06  2.47  2.48  2.39   2.40
 ...
 2021-01-28  2.18  2.23  2.18   2.20
 2021-01-29  2.19  2.21  2.11   2.14
 2021-02-01  2.08  2.09  1.93   1.94
}

```

股票数据下载后，使用`qt.get_table_info()`可以检查下载后数据表的信息，以及数据表中已经下载的数据量、占用空间、起止时间等信息：

```python
import qteasy as qt

qt.get_table_info('stock_daily')
```

```
<stock_daily>, 1.49GB/11.6M records on disc
primary keys: 
-----------------------------------
1:  ts_code:
    <unknown> entries
    starts: 000001.SZ, end: 873527.BJ
2:  trade_date:       *<CRITICAL>*
    <unknown> entries
    starts: 1990-12-19, end: 2023-02-01

columns of table:
------------------------------------
       columns       dtypes  remarks
0      ts_code  varchar(20)     证券代码
1   trade_date         date     交易日期
2         open        float      开盘价
3         high        float      最高价
4          low        float      最低价
5        close        float      收盘价
6    pre_close        float      昨收价
7       change        float      涨跌额
8      pct_chg        float      涨跌幅
9          vol       double   成交量(手)
10      amount       double  成交额(千元)
```
也可以使用`qt.get_table_overview()`来检查所有数据表的信息：
```python
import qteasy as qt

qt.get_table_overview()
```
```
Analyzing local data source tables... depending on size of tables, it may take a few minutes
[########################################]62/62-100.0%  Analyzing completed!
db:mysql://localhost@3306/ts_db
Following tables contain local data, to view complete list, print returned DataFrame
                 Has_data Size_on_disk Record_count Record_start  Record_end
table                                                                       
trade_calendar     True        2.5MB         73K     1990-10-12   2023-12-31
stock_basic        True        1.5MB          5K           None         None
stock_names        True        1.5MB         14K     1990-12-10   2023-07-17
stock_company      True       18.5MB          3K           None         None
stk_managers       True      150.4MB        126K     2020-01-01   2022-07-27
index_basic        True        3.5MB         10K           None         None
fund_basic         True        4.5MB         17K           None         None
future_basic       True        1.5MB          7K           None         None
opt_basic          True       15.5MB         44K           None         None
stock_1min         True      42.83GB      264.2M       20220318     20230904
stock_5min         True      34.33GB      231.4M       20090105     20230904
stock_15min        True      14.45GB      140.5M       20090105     20230904
stock_30min        True       7.78GB       76.8M       20090105     20230904
stock_hourly       True       4.22GB       41.9M       20090105     20230904
stock_daily        True       1.49GB       11.6M     1990-12-19   2023-09-18
stock_weekly       True      231.9MB        2.6M     1990-12-21   2023-07-14
stock_monthly      True       50.6MB        624K     1990-12-31   2023-06-30
index_1min         True       4.25GB       25.4M       20220318     20230904
index_5min         True       6.18GB       46.7M       20090105     20230904
index_15min        True       2.61GB       25.9M       20090105     20230904
index_30min        True      884.0MB       12.9M       20090105     20230904
index_hourly       True      536.0MB        7.6M       20090105     20230904
index_daily        True      309.0MB        3.7M     1990-12-19   2023-09-14
index_weekly       True       61.6MB        663K     1991-07-05   2023-07-14
index_monthly      True       13.5MB        156K     1991-07-31   2023-06-30
fund_1min          True      11.89GB       75.4M       20220318     20230904
fund_5min          True       3.68GB       12.3M       20220318     20230904
fund_15min         True       1.57GB        6.6M       20220318     20230904
fund_30min         True      750.9MB        2.9M       20220318     20230904
fund_hourly        True      124.8MB        1.5M       20210104     20230904
fund_daily         True      129.7MB        1.6M     1998-04-07   2023-09-14
fund_nav           True      693.0MB       13.9M     2000-01-07   2023-09-13
fund_share         True       72.7MB        1.4M     1998-03-27   2023-07-14
fund_manager       True      109.7MB         37K     2000-02-22   2023-03-30
future_hourly      True         32KB           0           None         None
future_daily       True      190.8MB        2.0M     1995-04-17   2023-09-14
options_hourly     True         32KB           0           None         None
options_daily      True      436.0MB        4.6M     2015-02-09   2023-09-14
stock_adj_factor   True      897.0MB       11.8M     1990-12-19   2023-09-14
fund_adj_factor    True       74.6MB        1.8M     1998-04-07   2023-09-14
stock_indicator    True       2.06GB       11.7M     1999-01-01   2023-09-18
stock_indicator2   True      734.8MB        4.1M     2017-06-14   2023-09-14
index_indicator    True        4.5MB         45K     2004-01-02   2023-09-14
index_weight       True      748.0MB        8.5M     2005-04-08   2023-07-14
income             True       59.7MB        213K     1990-12-31   2023-06-30
balance            True       97.8MB        218K     1989-12-31   2023-06-30
cashflow           True       69.7MB        181K     1998-12-31   2023-06-30
financial          True      289.0MB        203K     1989-12-31   2023-06-30
forecast           True       32.6MB         96K     1998-12-31   2024-03-31
express            True        3.5MB         23K     2004-12-31   2023-06-30
shibor             True         16KB         212           None         None
```

股票的数据下载后，使用`qt.candle()`可以显示股票数据K线图。


```python
data = qt.candle('000300.SH', start='2021-06-01', end='2021-8-01', asset_type='IDX')
```

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_5_2.png)
    

`qteasy`的K线图函数`candle`支持通过六位数股票/指数代码查询准确的证券代码，也支持通过股票、指数名称显示K线图
`qt.candle()`支持显示股票、基金、期货的K线，同时也可以传入`adj=b/f`参数显示复权价格，或传入`freq`参数改变K显得频率，显示分钟、
周或月K线，还可以传入更多的参数修改K线图上的
指标类型、移动均线类型以及参数，详细的用法请参考文档，示例如下：


```python
# 场内基金的小时K线图
qt.candle('159601', start = '20220121', freq='h')
# 沪深300指数的日K线图
qt.candle('000300', start = '20200121')
# 股票的30分钟K线，复权价格
qt.candle('中国电信', start = '20211021', freq='30min', adj='b')
# 期货K线，三条移动均线分别为9天、12天、26天
qt.candle('沪铜主力', start = '20211021', mav=[9, 12, 26])
# 场外基金净值曲线图，复权净值，不显示移动均线
qt.candle('000001.OF', start='20200101', asset_type='FD', adj='b', mav=[])
```

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_3_1.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_7_2.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_8_3.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_3_4.png)

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_3_5.png)
    


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

`qteasy`中的所有交易策略都是通过`qteast.Operator`（交易员）对象来实现回测和运行的，`Operator`对象是一个策略容器，一个交易员可以同时
管理多个不同的交易策略，哪怕这些交易策略有不同的运行时机和运行频率，或者不同的用途，例如一个策略用于选股、另一个策略用于大盘择时，再一个策
略用于风险控制，用户可以非常灵活地添加或修改`Operator`对象中的策略。

将策略交给`Operator`后，只要设置好交易的资产类别，资产池的大小，设定好每个策略的运行时机和频率后，`Operator`对象就会在合适的时间启动相应的
交易策略，生成策略信号，并将所有的策略信号混合(`blend`)后解析成为交易信号。

关于`Operator`对象的更多介绍，请参见`qteasy`文档

###  创建一个投资策略

`queasy`提供了两种方式创建交易策略：

- *使用内置交易策略组合*：
  - `qteasy`提供多种内置交易策略可供用户使用，不需要手工创建。通过引用内置策略的名称（关于所有内置策略的介绍，请参
  见详细文档）用户可以快速建立策略，还可以通过多个简单的策略混合成较为复杂的复合策略。
- *通过策略类自行创建策略*： 
  - 当用户的策略非常复杂时，可以通过`qteasy.Strategy`类来自定义一个策略。

### 生成一个DMA均线择时交易策略
在这里，我们将使用一个内置的`DMA`均线择时策略来生成一个最简单的大盘择时交易系统。所有内置交易策略的清单和详细说明请参见文档。

创建`Operator`对象时传入参数：`strategies='DMA'`，新建一个`DMA`双均线择时交易策略。
创建好`Operator`对象后，可以用`op.info()`来查看它的信息。

```python
import qteasy as qt

op = qt.Operator(strategies='dma')
op.info()
```
```
            -----------------------Operator Information-----------------------
Strategies:  1 Strategies
Run Mode:    batch - All history operation signals are generated before back testing
Signal Type: pt - Position Target, signal represents position holdings in percentage of total value

            ------------------------Strategy blenders-------------------------
for strategy running timing - close:
no blender

            ----------------------------Strategies----------------------------
id        name                  run timing   data window       data types             parameters     
____________________________________________________________________________________________________
dma       DMA                  days @ close  270 x days        ['close']            (12, 26, 9)     
====================================================================================================

```
`Operator`中每一个交易策略都会被赋予一个唯一的`ID`，我们看到`op`中有一个交易策略，ID是`dma`，我们在`Operator`层面设置或修改策略的参数
时，都需要引用这个`ID`。

`DMA`是一个内置的均线择时策略，它通过计算股票每日收盘价的快、慢两根移动均线的差值`DMA`与其移动平均值`AMA`之间的交叉情况来确定多空或买卖
点，这个策略需要三个**可调参数**`(s,l,d)`，公式如下：

- DMA = 股价的s日均线 - 股价的l日均线
- AMA = DMA的d日均线

>- **可调参数**: 是由用户定义的策略的运行参数。`qteasy`可以识别策略的可调参数，并且设计了多种优化算法，通过改变可调参数来调整策略
   > 的运行性能，从而达到优化策略表现的目的

DMA是一个内置策略，qteasy已经定义好了交易规则：
 
>1. DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线，由空变多，产生买入信号
>2. DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线，由多变空，产生卖出信号

在默认情况下，三个**可调参数**为：`(12,26,9)`, 但我们可以给出任意大于2小于250的三个整数作为策略的参数，以适应不同交易活跃度的股票、或者适应
不同的策略运行周期。

除了DMA策略以外，`qteasy`还提供了其他择时策略，使用qt.built_ins()可以查看所有内置策略的清单，或者某一个内置策略的详细信息：

```python
import qteasy as qt

qt.built_ins('finance')
```
得到：

```
 以股票过去一段时间内的财务指标的平均值作为选股因子选股
        基础选股策略：以股票的历史指标的平均值作为选股因子，因子排序参数可以作为策略参数传入
        改变策略数据类型，根据不同的历史数据选股，选股参数可以通过pars传入

    策略参数：(参数含义与FactorSorter策略的属性一致)
        sort_ascending: enum, 是否升序排列因子
        weighting, enum, 股票仓位分配比例权重
        condition, enum, 股票筛选条件
        lbound: float, 股票筛选下限值
        ubound: float, 股票筛选上限值
        max_sel_count: float, 抽取的股票的数量(p>=1)或比例(p<1)
    信号类型：
        PT型：百分比持仓比例信号
    信号规则：
        使用data_types指定一种数据类型，将股票过去的datatypes数据取平均值，将该平均值作为选股因子进行选股
        通过以下策略属性控制选股方法：
        *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
        *condition:         str ,   确定股票的筛选条件，默认值'any'
                                    'any'        :默认值，选择所有可用股票
                                    'greater'    :筛选出因子大于ubound的股票
                                    'less'       :筛选出因子小于lbound的股票
                                    'between'    :筛选出因子介于lbound与ubound之间的股票
                                    'not_between':筛选出因子不在lbound与ubound之间的股票
        *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
        *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
        *sort_ascending:    bool,   排序方法，默认值: False,
                                    True: 优先选择因子最小的股票,
                                    False, 优先选择因子最大的股票
        *weighting:         str ,   确定如何分配选中股票的权重
                                    默认值: 'even'
                                    'even'       :所有被选中的股票都获得同样的权重
                                    'linear'     :权重根据因子排序线性分配
                                    'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                    'proportion' :权重与股票的因子分值成正比

    策略属性缺省值：
    默认参数：(True, 'even', 'greater', 0, 0, 0.25)
    数据类型：eps 每股收益，单数据输入
    采样频率：年
    窗口长度：270
    参数范围：[(True, False),
             ('even', 'linear', 'proportion'),
             ('any', 'greater', 'less', 'between', 'not_between'),
             (-np.inf, np.inf),
             (-np.inf, np.inf),
             (0, 1.)]
    策略不支持参考数据，不支持交易数据
```

传递策略参数到`op`对象中：


```python
op.set_parameter('dma', pars=(23, 166, 196))
```

上面的代码将参数`pars=(23, 166, 196)`传递给`DMA`策略，`op.set_parameter()`的详细使用方法见手册。


### 回测并评价交易策略的性能表现

使用默认参数回测策略在历史数据上的表现，请使用`op.run()`，`qteasy`使用环境变量来控制运行的各种参数，现在可以直接在`op.run()`的
运行参数中直接配置各种环境变量，更多关于环境变量的信息，请参见文档。下面的代码可以直接开始回测并评价结果：

- 配置环境变量`mode=1`表示进入回测模式
- `invest_start/end`: 回测模拟交易开始/结束日期
- 环境变量`visual`控制是否输出可视化图表



```python
res = op.run(mode=1, 
             invest_start='20080101', 
             invest_end='20210201',
             visual=True)
```

输出结果如下：
```
====================================
|                                  |
|       BACK TESTING RESULT        |
|                                  |
====================================
qteasy running mode: 1 - History back testing
time consumption for operate signal creation: 3.3ms
time consumption for operation back looping:  348.3ms

investment starts on      2008-01-02 00:00:00
ends on                   2021-02-01 00:00:00
Total looped periods:     13.1 years.

-------------operation summary:------------

           Sell   Buy  Total  Long pct  Short pct  Empty pct
000300.SH    11    12     23     50.7%       0.0%      49.3%   

Total operation fee:      ¥    1,042.59
total investment amount:  ¥  100,000.00
final value:              ¥  425,982.00
Total return:                   325.98% 
Avg Yearly return:               11.70%
Skewness:                         -0.63
Kurtosis:                         10.80
Benchmark return:                 0.60% 
Benchmark Yearly return:          0.05%

------strategy loop_results indicators------ 
alpha:                            0.067
Beta:                             1.002
Sharp ratio:                      0.041
Info ratio:                       0.029
250 day volatility:               0.162
Max drawdown:                    35.04% 
    peak / valley:        2009-08-03 / 2014-07-10
    recovered on:         2014-12-16

===========END OF REPORT=============
```
![png](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_14_3.png)
整个回测过程耗时0.4s左右，其中交易信号生成共耗费3.3ms，交易回测耗时348ms

根据上面结果，系统使用了沪深300指数从2008年到2021年共13.1年的历史数据来测试策略，在这段时间内，模拟2008年1月1日投入10万元投资
于沪深300指数，共产生了11次买入信号和12次卖出信号，产生的交易费用为1042.59元。
到2021年2月1日为止，投资总额从10万元变为42万元，投资总收益为325.98%，年化收益率为11.78%，而同期沪深300指数本身的涨幅仅为0.6%，策略最终是跑赢了大盘的。

在`qteasy`模拟的交易过程中，可以设置丰富的参数，例如：

- 投入资金的数量、日期、或者设置分批多次投入资金；
- 买入和卖出交易的费用、包括佣金费率、最低费用、固定费用、以及滑点。各种费率都可以针对买入和卖出分别设定
- 买入和卖出交易的交割时间，也就是T+N日交割制度
- 买入和卖出交易的最小批量，例如是否允许分数份额交易、还是必须整数份额、甚至整百份交易

最终打印的回测结果是考虑上述所有交易参数之后的最终结果，因此可以看到总交易成本。详细的交易参数设置请参见详细文档。

另外，`qteasy`还给给出了关于策略表现的几个指标：
如alpha和beta分别是0.067和1.002，而夏普率为0.041。最大回撤发生在2009年8月3日到2014年7月10日，回撤了35.0%，且到了2014年12月16日才翻盘。

在上面的回测结果中我们给出了参数`visual=False`，如果令`visual=True`，就能得到可视化的回测结果，以图表的形式给出，并提供可视化信息：

- 投资策略的历史资金曲线
- 参考数据（沪深300指数）的历史曲线
- 买点和卖点（在参考数据上以红色、绿色箭头显示）
- 持仓区间（绿色表示持仓）
- 投资策略的评价指标（alpha、sharp等）
- 历史回撤分析（显示五次最大的回撤）
- 历史收益率热力图、山积图等图表


`qteasy`提供了丰富的策略回测选项，例如：

- 回测开始结束日期
- 回测结果评价指标
- 回测时是否允许持有负数仓位（用于模拟期货交易卖空行为，也可以使用专门的期货交易模拟算法）

更多的选项请参见详细文档


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


```commandline
Welcome to TraderShell! currently in dashboard mode, live status will be displayed here.
You can not input commands in this mode, if you want to enter interactive mode, pleasepress "Ctrl+C" to exit dashboard mode and select from prompted options.

[2023-09-19 22:04:19]-sleeping: will execute next task:(None) in about 2 hours

```
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

```commandline
Welcome to the trader shell interactive mode. Type help or ? to list commands.
Type "bye" to stop trader and exit shell.
Type "dashboard" to leave interactive mode and enter dashboard.
Type "help <command>" to get help for more commands.

(QTEASY) overview
Account Overview:
-----------------
Account ID:                     1
User Name:                      user_name
Created on:                     2023-07-20 22:37:35
Own Cash:                       ¥ 740,003.49 
Available Cash:                 ¥ 740,003.49
Total Investment:               ¥ 1,000,000.00
Total Value:                    ¥ 966,584.64
Total Stock Value:              ¥ 226,581.15
Total Profit:                   ¥ -682.76

(QTEASY) orders 000651 today
    symbol position direction order_type      qty  price_quoted      submitted_time    status  price_filled  filled_qty  canceled_qty      execution_time delivery_status
 000651.SZ     long      sell     market  15260.0         36.28 2023-09-18 14:59:07  canceled         36.28         0.0       15260.0 2023-09-18 15:05:01              DL
 000651.SZ     long      sell     market  15259.0         36.15 2023-09-19 14:59:07    filled         36.06      7600.0           0.0 2023-09-19 14:59:15              DL
 000651.SZ     long      sell     market  15259.0         36.15 2023-09-19 14:59:07    filled         35.82      7600.0           0.0 2023-09-19 14:59:16              DL
 000651.SZ     long      sell     market  15259.0         36.15 2023-09-19 14:59:07    filled         35.48        59.0           0.0 2023-09-19 14:59:17              DL
(QTEASY) 

```
在命令行模式下可以与`TraderShell`实现交互，操作当前账户，查询交易历史、修改状态等：

- `pause` / `resume`: 暂停/重新启动交易策略
- `change`: 修改当前持仓和现金余额
- `positions`: 查看当前持仓
- `orders`: 查看当前订单
- `history`: 查看历史交易记录
- `exit`: 退出TraderShell
- ... 更多`TraderShell`命令参见`QTEASY`文档

### 回测并优化交易策略

交易策略的表现往往与参数有关，如果输入不同的参数，策略回报相差会非常大。因此我们在定义策略的时候，可以将这些参数定义为"可调参数"。
定义好可调参数后，`qteasy`就可以用多种不同的优化算法，帮助搜索最优的策略参数，并且提供多种不同的策略参数检验方法，为策略参数的表
现提供独立检验。

要使用策略优化功能，需要设置交易策略的优化标记`opt_tag=1`，这样可以单独开启`Operator`对象中某一个或某几个策略的优化标记，从而在
对某些策略的可调参数进行优化的同时，其他策略的参数保持不变。然后运行`qt.run()`,并配置环境变量`mode=2`即可:

```python
import qteasy as qt

op = qt.Operator(strategies='dma')
op.set_parameter('dma', opt_tag=1)
res = qt.run(op, mode=2, visual=True)
```

默认情况下，`qteasy`将在同一段历史数据上反复回测，找到结果最好的30组参数，并把这30组参数在另一段历史数据上进行独立测试，并显
示独立测试的结果，同时输出可视化结果如下：

这里忽略详细的参数对比数据，详细的结果解读和说明参见详细文档

关于策略优化结果的更多解读、以及更多优化参数的介绍，请参见详细文档

![png](https://raw.githubusercontent.com/shepherdpp/qteasy/qt_dev/img/output_15_3.png)   
