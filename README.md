# qteasy -- 一个基于Python的高效量化投资工具包

- Author: **Jackie PENG**

- email: *jackie_pengzhao@163.com* 

- Created: 2019, July, 16

## 安装及依赖包
这个项目依赖以下python package:
- *`pandas` version ~= 0.25.1*    `# conda install pandas`
- *`numpy` version ~= 1.18.1*    `# conda install numpy`
- *`numba` version ~= 0.47.0*    `# conda install numba`
- *`TA-lib` version ~= 0.4.18*    `# conda install -c conda-forge ta-lib`
- *`tushare` version ~= 1.2.89*    `# pip install tushare`
- *`mplfinance` version ~= 0.12.7*    `# conda install -c conda-forge mplfinance`
- *`pymysql`*    `# optional for datasource type database, conda install -c anaconda pymysql`
- *`sqlalchemy`* version ~= 1.4.22   `# optional for datasource type database, conda install sqlalchemy`
- *`pytables`* version ~= 3.6.1  `# optional for datasource file type "hdf", conda install -c conda-forge pytables`
- *`pyarrow`* version ~= 3.0.0   `# optional for datasource file type "feather", conda install -c conda-forge pyarrow`

## 介绍

本项目旨在开发一套基于python的本地运行的量化交易策略回测和开发工具，包含以下基本功能

1. 金融历史数据的获取、清洗、整理、可视化、本地存储查询及应用，并计划提供一些金融统计数据分析工具
2. 投资交易策略的创建、回测、性能评价，并且通过定义策略的可调参数，提供多种优化算法实现交易策略的参数调优
3. 交易策略的部署、实时运行，未来还将实现与自动化交易系统连接、实现自动化交易


开发本模块的目标是为量化交易人员提供一套策略开发框架，回测速度快、回测精度高、评价指标全，而且可以非常灵活地实现各种自定义交易策略

##  10分钟了解qteasy的功能

- 模块的导入
- 数据的获取和可视化  
- 投资策略的创建
- 投资策略的回测
- 投资策略的优化

基本的模块导入方法如下

```python
import qteasy as qt
```

模块导入后，工具包中的函数及对象即可以使用了:


```python
ht = qt.HistoryPanel()
op = qt.Operator()
```

### 下载股票价格数据并将其可视化 
为了使用`qteasy`，需要大量的金融历史数据，所有的历史数据都必须首先保存在本地，通过一个DataSource对象来获取。这些数据可以生成投资策略所需要的历史数据组合，也可以通过简单的命令生成股票的K线图，如果本地没有历史数据，那么qteasy的许多功能就无法执行。

为了使用历史数据，`qteasy`支持通过`tushare`金融数据包来获取大量的金融数据，用户需要自行获取相应的权限和积分（详情参考：https://tushare.pro/document/2）
一旦拥有足够的权限，可以通过下面的命令批量拉取过去一年的所有金融数据并保存在本地，以确保`qteasy`的相关功能可以正常使用
（请注意，由于数据量较大，下载时间较长，建议分批下载。建议使用数据库保存本地数据，不包括分钟数据时，所有数据将占用大约10G的磁盘空间，
分钟级别数据将占用350GB甚至更多的磁盘空间）。
关于`DataSource`对象的更多详细介绍，请参见详细文档。

```python
qt.QT_DATA_SOURCE.refill_data_source('all', start_date='20210101', end_date='20220101')
```

股票的数据下载后，使用`candle()`函数，如果K线图显示成功，表明价格数据下载成功。


```python
data = qt.candle('000300.SH', start='2021-06-01', end='2021-8-01', asset_type='IDX')
```

![png](img/output_5_2.png)
    

`qteasy`的K线图函数`candle`支持通过六位数股票/指数代码查询准确的证券代码，也支持通过股票、指数名称显示K线图
`qt.candle()`支持显示股票、基金、期货的K线，同时也可以传入`adj`参数显示复权价格，或传入`freq`参数改变K显得频率，显示分钟、周或月K线，还可以传入更多的参数修改K线图上的
指标类型、移动均线类型以及参数，详细的用法请参考文档，示例如下：


```python
# 场内基金的小时K线图
data = qt.candle('159601', start = '20220121', freq='h')
# 沪深300指数的日K线图
data = qt.candle('000300', start = '20200121')
# 股票的30分钟K线，复权价格
data = qt.candle('中国电信', start = '20211021', freq='30min', adj='b')
# 期货K线，三条移动均线分别为9天、12天、26天
data = qt.candle('沪铜主力', start = '20211021', mav=[9, 12, 26])
# 场外基金净值曲线图，复权净值，不显示移动均线
data = qt.candle('000001.OF', start='20200101', asset_type='FD', adj='b', mav=[])
```

![png](img/output_3_1.png)

![png](img/output_7_2.png)

![png](img/output_8_3.png)

![png](img/output_3_4.png)

![png](img/output_3_5.png)
    


生成的K线图可以是一个交互式动态K线图（请注意，K线图基于`matplotlib`绘制，在使用不同的终端时，显示功能有所区别，某些终端并不支持动态图表，详情请参阅https://matplotlib.org/stable/users/explain/backends.html），在使用动态K线图时，用户可以用鼠标和键盘控制K线图的显示范围：

- 鼠标在图表上左右拖动：可以移动K线图显示更早或更晚的K线
- 鼠标滚轮在图表上滚动，可以缩小或放大K线图的显示范围
- 通过键盘左右方向键，可以移动K线图的显示范围显示更早或更晚的K线
- 通过键盘上下键，可以缩小或放大K线图的显示范围
- 在K线图上双击鼠标，可以切换不同的均线类型
- 在K线图的指标区域双击，可以切换不同的指标类型：MACD，RSI，DEMA

![gif](img/output_dyna_plot.gif)

###  创建一个投资策略，进行回测评价并优化其表现

`queasy`提供了多种内置交易策略可供用户使用，因此用户不需要手工创建这些策略，可以直接使用内置策略（关于所有内置策略的介绍，请参见详细文档）。复合策略可以通过多个简单的策略混合而成。当复合策略无法达到预计的效果时，可以通过`qteasy.Strategy`类来自定义一个策略。

### Create a DMA timing strategy  生成一个DMA均线择时交易策略

`qteasy`中的所有交易策略都是通过`qteast.Operator`对象来实现回测和运行的，每一个`Operator`对象均包含三种不同的交易策略用途，每一种用途用于生成不同类型的交易信号，以便用于交易的模拟，例如选股信号、择时信号或者风控信号，每种信号类型都可以由一个或多个交易策略来生成，在后面的章节中我们可以详细介绍每一种信号类型以及交易策略，在这里，我们将使用一个内置的DMA均线择时策略来生成一个择时信号，忽略选股和风控信号。

创建一个`Operator`对象，并在创建时传入参数：`strategies='DMA'`，新建一个DMA双均线择时交易策略。


```python
op = qt.Operator(strategies='dma')
```

DMA是一个内置的均线择时策略，它通过计算股票每日收盘价的快、慢两根移动均线的差值DMA与其移动平均值AMA之间的交叉情况来确定多空或买卖
点，这个策略需要三个参数`(s,l,d)`，公式如下：

- DMA = 股价的s日均线 - 股价的l日均线
- AMA = DMA的d日均线

交易规则：

        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线，由空变多，产生买入信号
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线，由多变空，产生卖出信号

在默认情况下，三个参数为：`(12,26,9)`, 但我们可以给出任意大于2小于250的三个整数作为策略的参数，以适应不同交易活跃度的股票、或者适应
不同的策略运行周期。除了DMA策略以外，`qteasy`还提供了其他择时策略，详细的列表可以参见`qteasy`的手册。

传递策略参数到`op`对象中：


```python
op.set_parameter('dma', pars=(23, 166, 196))
```

上面的代码将参数`pars=(23, 166, 196)`传递给DMA策略，`op.set_parameter()`的详细使用方法见手册。


### Back-test strategy  回测并评价交易策略的性能表现

使用默认参数回测策略在历史数据上的表现，请使用`qteasy.run()`，`mode=1`表示进入回测模式，传入参数`visual=False`以文本形式打印结果
`qteasy.run()`的其他可选参数参见手册


```python
res = qt.run(op, mode=1, invest_start='20080101', visual=True)
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

整个回测过程耗时0.4s左右，其中交易信号生成共耗费3.3ms，交易回测耗时348ms

根据上面结果，系统使用了沪深300指数从2008年到2021年共13.1年的历史数据来测试策略，在这段时间内，模拟2008年1月1日投入10万元投资于沪深300指数，共产生了11次买入信号和12次卖出信号，产生的交易费用为1042.59元。
到2021年2月1日为止，投资总额从10万元变为42万元，投资总收益为325.98%，年化收益率为11.78%，而同期沪深300指数本身的涨幅仅为0。6%，策略最终是跑赢了大盘的。

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

![png](img/output_14_3.png)
qteasy提供了丰富的策略回测选项，例如：

- 回测开始结束日期
- 回测结果评价指标
- 回测时是否允许持有负数仓位（用于模拟期货交易卖空行为，也可以使用专门的期货交易模拟算法）

更多的选项请参见详细文档

### Optimize strategy  回测并优化交易策略

交易策略的表现往往与参数有关，例如上个例子中的DMA择时策略，如果输入不同的参数，策略回报相差会非常大。qteasy提供了多种不同的策略参数优化算法，帮助搜索最优的策略参数，并且提供多种不同的策略参数检验方法，为策略参数的表现提供独立检验。

要使用策略优化功能，需要设置交易策略的优化标记`opt_tag=1`：然后运行`qt.run()`,并使用参数`mode=2`即可:

```python
op.set_parameter('dma', opt_tag=1)
res = qt.run(op, mode=2, visual=True)
```

默认情况下，qteasy将在同一段历史数据上反复回测，找到结果最好的30组参数，并把这30组参数在另一段历史数据上进行独立测试，并显示独立测试的结果，同时输出可视化结果如下：

这里忽略详细的参数对比数据，详细的结果解读和说明参见详细文档

关于策略优化结果的更多解读、以及更多优化参数的介绍，请参见详细文档

![png](img/output_15_3.png)   

