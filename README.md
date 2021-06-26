# qteasy -- a python-based fast quantitative investment utility module 一个基于Python的高效量化投资工具包

- Author: **Jackie PENG**

- email: *jackie_pengzhao@163.com* 

- Project created on: 2019, July, 16

## Installation and dependencies 安装及依赖包
This project requires and depends on following packages:
- *`pandas` version 0.25*
- *`numpy` version 0.19*
- *`TA-lib` version 0.4*
- *`tushare pro` version 1.24.1*
- *`matplotlib.mplfinance` version 0.12*

## Introductions 介绍

This project is aiming at a fast quantitative investment package for python, with following functions:

1. Historical stock data acquiring and bundling, visualization
2. Investment strategy creation, backtesting, assessment and optimization
3. Live stock trading: trading operation submission, withdrawal, status checking and feedback reporting

The target of this module is to provide effective vectorized backtesting and assessment of investment 
strategies, with highly versertility and flexibility

## Contents and Tutorials 内容及教程

- basic usage 基本使用方法
- data acquiring 数据的获取和可视化  
- strategy creation 投资策略的创建
- Back-test of strategies 投资策略的回测
- Strategy Optimization 投资策略的优化

## Gets to know what-can-do of  qteasy in 10 Min, 10分钟了解qteasy的功能
The convensional way of importing this package is following:
基本的模块导入方法如下

```python
import qteasy as qt
```
Then the classes and functions can be used 模块导入后，工具包中的函数及对象即可以使用了:

```python
import qteasy as qt
ht = qt.HistoryPanel()
op = qt.Operator()
```
### Load and visualize Stock prices 下载股票价格数据并将其可视化 
With `qteasy`, historical stock price data can be easily loaded and displayed, with a series of functions that helps visualizing price data. for example:

使用`qteasy`，可以借助`tushare`模块下载需要的股票历史数据，生成投资策略所需要的历史数据组合，也可以通过简单的命令生成股票的K线图：
```python
qt.candle('513100.SZ', start='2020-12-01', asset_type='FD')
```
a dynamic candle chart of stock 000300 will be displayed, you can drag the candle plots over to view wider span of data, zoom
in and out with scrolling of your mouse, and switching bewteen multiple indicator lines by double clicking the chart

生成的K线图是一个交互式动态K线图，用户可以用鼠标在图表上拖动，移动K线图显示更早或更晚的K线，也可以通过鼠标滚轮缩放K线。另外，在K线图上双击鼠标，可以切换不同的
均线或指标

![dynamic candle plot of 000300](https://img-blog.csdnimg.cn/20210611111331946.gif#pic_center)

### Create and running of investment strategy sessions  创建一个投资策略，进行回测评价并优化其表现

There are multiple internally preset strategies such as crossline timing strategy or DMA timing strategy provided in
 qteasy, a strategy should be created with an Operator object, the Operator is the container of strategies, and provides
 multiple methods to utilize and operate on these strategies.

queasy提供了多种内置交易策略可供用户使用，因此用户不需要手工创建这些策略，直接使用即可。复合策略可以通过多个简单的策略混合而成。当复合策略无法达到
预计的效果时，可以通过qteasy.strategy类来自定义一个策略。
 
### Create a DMA timing strategy  生成一个DMA均线择时交易策略

`qteasy`中的所有交易策略都是通过`qteast.Operator`对象来实现回测和运行的，每一个`Operator`对象均包含三种不同的交易策略用途，每一种用途用于生成
不同类型的交易信号，以便用于交易的模拟，例如选股信号、择时信号或者风控信号，每种信号类型都可以由一个或多个交易策略来生成，在后面的章节中我们可以
详细介绍每一种信号类型以及交易策略，在这里，我们将使用一个内置的DMA均线择时策略来生成一个择时信号，忽略选股和风控信号。

创建一个`Operator`对象，并在创建时传入参数：`timing_types='DMA'`，新建一个DMA双均线择时交易策略。

 ```python
import qteasy as qt

op = qt.Operator(timing_types='DMA')
```

DMA是一个内置的均线择时策略，它通过计算股票每日收盘价的快、慢两根移动均线的差值DMA与其移动平均值AMA之间的交叉情况来确定多空或买卖
点，这个策略需要三个参数（s,l,d），公式如下：

- DMA = 股价的s日均线 - 股价的l日均线
- AMA = DMA的d日均线

交易规则：

        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线，由空变多，产生买入信号
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线，由多变空，产生卖出信号

在默认情况下，三个参数为：（12,26,9）, 但我们可以给出任意大于2小于250的三个整数作为策略的参数，以适应不同交易活跃度的股票、或者适应
不同的策略运行周期。除了DMA策略以外，qteasy还提供了其他择时策略，详细的列表可以参见qteasy的手册。

传递策略参数到op对象中：

```python
op.set_parameter('t-0', pars=(23, 166, 196))
op.set_parameter('s-0', (0.5,))
op.set_parameter('r-0', ())
```

上面的带把把参数`pars=(23, 166, 196)`传递给DMA策略，`op.set_parameter()`的详细使用方法见手册。


#### Back-test strategy
#### 回测并评价交易策略的性能表现

使用默认参数回测策略在历史数据上的表现，请使用`qteasy.run()`，`mode=1`表示进入回测模式，传入参数`visual=False`以文本形式打印结果
`qteasy.run()`的其他可选参数参见手册

```python
res = qt.run(op, mode=1, visual=False)
```
得到：

```
     ==================================== 
     |                                  |
     |       BACK TESTING RESULT        |
     |                                  |
     ====================================

qteasy running mode: 1 - History back testing
time consumption for operate signal creation: 11.1ms
time consumption for operation back looping:  70.7ms

investment starts on      2016-04-05 00:00:00
ends on                   2021-02-01 00:00:00
Total looped periods:     4.2 years.
-----------operation summary:-----------
            sell  buy  total
000300.SH   6.0  6.0   12.0
Total operation fee:     ¥      282.43
total investment amount: ¥  100,000.00
final value:             ¥  184,052.82
Total return:                    84.05% 
Avg Yearly return:               15.63%
Reference return:                65.96% 
Reference Yearly return:         11.06%
------strategy loop_results indicators------ 
alpha:                            0.026
Beta:                             0.982
Sharp ratio:                      0.524
Info ratio:                       0.008
250 day volatility:               0.191
Max drawdown:                    17.755% 
    from:                 2019-04-19 to 2020-02-03
    recovered on:         2020-07-06

===========END OF REPORT=============
```
回测过程中，交易信号生成共耗费11ms，回测耗时70ms

根据上面结果，系统使用了沪深300指数从2016年到2021年共4.2年的历史数据来测试策略，在这段时间内，模拟2016年4月5日投入10万元
投资于沪深300指数，共产生了6次买入信号和6次卖出信号。

到2021年2月1日为止，投资总收益为84.05%，年化收益率为15.63%，而同期沪深300指数本身的涨幅为65%，该策略最终是跑赢了
大盘的。

另外，qteasy还给给出了关于策略表现的几个指标：
如alpha和beta分别是0.026和0.982，而夏普率为0.524。最大回撤发生在2019年4月19日到2020年2月3日，回撤了17.8%，且到了2020年7月6日才
翻盘。

在上面的回测结果中我们给出了参数`visual=False`，如果令`visual=True`，就能得到可视化的回测结果，
默认情况下，回测结果会以图表的形式给出：

![back testing visual result](https://user-images.githubusercontent.com/34448648/123515365-acc08200-d6c9-11eb-9ae5-fcc1199f3d8b.png)

图表中除了显示完整的资金曲线外，还可以显示参考指标的收益曲线、买卖点，仓位、最大回撤、每日收益等信息

未来在可视化图表中还会加入更多的回测指标和可视化图表。

如果要自定义区间起止日期，需要在`qteasy.run()`的参数中指定`invest_start, invest_end`等参数
即可：

```python
res=qt.run(op, 
           asset_pool='000300.SH', 
           asset_type='I',
           invest_start = '20080312')
```

上面的参数指定了回测过程的投资股票池为`asset_pool='000300.SH'`，更多的参数选项参见手册。

运行上述代码后，得到下面结果：

![back test result 2](https://user-images.githubusercontent.com/34448648/123509564-c56c7000-d6a8-11eb-84cf-9bf5ad15e592.png)

这次回测使用了从2008年开始的共12年的数据，总回报率为440%左右，因为我们从08年的历史高点开始回测的，因此同期的沪深300的收益率只有25%，年化
收益的差异更大，从曲线图上也能看出，策略跑赢了大盘。

#### Optimization of stratepltgies
#### 策略表现的优化

策略的表现与许多因素有关，其中最重要的就是策略的参数。使用较长的均线参数可能会让策略在较长的交易周期中保持盈利，但是可能对短期波动的捕捉却
无能为力，而较短的均线可能可以快速应对股价的变化，但是也有可能导致大量无效的假信号，白白浪费交易成本。因此，通过改变策略的参数来改变或优化
其表现，或者根据投资周期、股票类型、交易波动程度、风险偏好、交易费率高低来找到潜在最优的参数组合，是策略优化的关键。

`qteasy`提供了简单明了的交易策略优化方法，并且提供了可视化的交易策略优化性能比较工具，有助于帮助找到最优的交易策略参数。

在同一段历史数据区间上搜索DMA策略的最佳参数，并在一段独立的历史区间上测试其表现：

```python
op.set_parameter('t-0', opt_tag=1)
res = qt.run(op, mode=2)
```

`opt_tag=1`是一个关键参数，它告诉`qteasy`需要对DMA策略进行参数寻优优化。

优化的过程同样用`qt.run()`来启动，不同的是`mode=2`。输出在同一个历史区间上表现最佳的30组参数，并把他们的表现用可视化图表展示出来：

![Optimization output](https://user-images.githubusercontent.com/34448648/123515721-29079500-d6cb-11eb-9e6f-e439a5e1563d.png)

注意红色线条代表的30组参数是在2016年到2019年的历史数据上"训练"出来的，为了验证其真实的表现，这30组数据会被用于2020年到2021年的历史数据
中检验其表现，通过这样的独立测试后的策略，才能体现出用在未来的交易中的价值。

换言之，通过独立检验的策略参数更有可能在未来带来更好的表现。
