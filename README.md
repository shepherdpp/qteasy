## qteasy
### a python-based fast quantitative investment utility module for investment strategy creating, backtesting, optimization and implementation
### 一个基于Python的高效量化投资工具包，用于投资策略的创建、回测、优化以及部署

Author: **Jackie PENG**

email: *jackie_pengzhao@163.com* 

Project created on: 2019, July, 16

### Installation and dependencies 安装及依赖包
This project requires and depends on following packages:
- *`pandas` version 0.25*
- *`numpy` version 0.19*
- *`TA-lib` version 0.4*
- *`tushare pro` version 1.24.1*
- *`matplotlib.mplfinance` version 0.12*

### Introductions 介绍

This project is aiming at a fast quantitative investment package for python, with following functions:

1. Historical stock data acquiring and bundling, visualization
2. Investment strategy creation, backtesting, assessment and optimization
3. Live stock trading: trading operation submission, withdrawal, status checking and feedback reporting

The target of this module is to provide effective vectorized backtesting and assessment of investment 
strategies, with highly versertility and flexibility

### Contents and Tutorials 内容及教程

- basic usage 基本使用方法
- data acquiring 数据的获取和可视化  
- strategy creation 投资策略的创建
- Back-test of strategies 投资策略的回测
- Strategy Optimization 投资策略的优化

### Basic usage: A 10-min introduction to qteasy 
### 基本使用方法，10分钟熟悉qteasy的使用
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
#### Load and visualize Stock prices 下载股票价格数据并将其可视化 
With `qteasy`, historical stock price data can be easily loaded and displayed, with a series of functions that helps visualizing price data. for example:
使用qteasy，可以借助tushare模块下载需要的股票历史数据，生成投资策略所需要的历史数据组合，也可以通过简单的命令生成股票的K线图：
```python
qt.candle('513100.SZ', start='2020-12-01', asset_type='FD')

```
a dynamic candle chart of stock 000300 will be displayed, you can drag the candle plots over to view wider span of data, zoom
in and out with scrolling of your mouse, and switching bewteen multiple indicator lines by double clicking the chart
生成的K线图是一个交互式动态K线图，用户可以用鼠标在图表上拖动，移动K线图显示更早或更晚的K线，也可以通过鼠标滚轮缩放K线。另外，在K线图上双击鼠标，可以切换不同的
均线或指标

![dynamic candle plot of 000300](https://img-blog.csdnimg.cn/20210611111331946.gif#pic_center)

#### Create and running of investment strategy sessions
#### 创建一个投资策略，进行回测评价并优化其表现

In this section, a short and simple example will be given for the readers to go through the process of creating a 
strategy, testing it throught back-testing function, and searching for parameters that allows the strategy to provide 
the best output with given historical data.

本节将通过一个简单的例子演示如何通过qtease创建一个基于均线的股票择时策略，设置策略的参数，获取历史数据并进行回测，进行回测结果的评价输出、并进行结果的
优化

There are multiple internally preset strategies such as crossline timing strategy or DMA timing strategy provided in
 qteasy, a strategy should be created with an Operator object, the Operator is the container of strategies, and provides
 multiple methods to utilize and operate on these strategies.

queasy提供了多种内置交易策略可供用户使用，因此用户不需要手工创建这些策略，直接使用即可。复合策略可以通过多个简单的策略混合而成。当复合策略无法达到
预计的效果时，可以通过qteasy.strategy类来自定义一个策略。
 
 An Opertor with a DMA strategy can be created like this:
下面通过一个简单的DMA择时策略的创建、回测和优化来展示queasy的使用过程；
 
#### Timing strategy Example: Cross-Line strategy
#### 使用内置策略生成一个DMA均线择时策略并设置策略参数

In this section,  a cross-line timing strategy will be created, as a demonstration of how a strategy can be created
through internally defined strategies, and how to set up the strategy with a Operator() object.

qteasy中的所有交易策略都是通过qteast.Operator对象来实现回测和运行的，每一个Operator对象均包含三种不同的交易策略用途，每一种用途用于生成
不同类型的交易信号，以便用于交易的模拟，例如选股信号、择时信号或者风控信号，每种信号类型都可以由一个或多个交易策略来生成，在后面的章节中我们可以
详细介绍每一种信号类型以及交易策略，在这里，我们将使用一个内置的DMA均线择时策略来生成一个择时信号，忽略选股和风控信号。

我们可以通过以下代码创建一个Operator对象。

 ```python
import qteasy as qt

op = qt.Operator(timing_types='DMA')
```
在创建Operator对象的时候，我们通过`timing_types='DMA'`就创建一个DMA均线择时策略，DMA是一个内置的均线择时策略，通过计算股票每日收盘价
的快、慢两根移动均线的差值DMA与其移动平均值AMA两根线之间的交叉情况来确定多空或买卖点的一种择时策略，它的计算需要三个参数（s,l,d），公式如下：
DMA = 股价的s日均线 - 股价的l日均线
AMA = DMA的d日均线
生成DMA多空判断：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, 由空变多，产生买入信号
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线，由多变空，产生卖出信号

根据上述定义，DMA择时交易策略需要三个参数（s,l,d）以生成交易信号，在默认情况下，三个参数为：（12,26,9）, 但我们可以给出任意大于2小于250的
三个整数作为策略的参数，以适应不同交易活跃度的股票、或者适应不同的策略运行周期。当然，除了DMA策略以外，qteasy还提供了其他择时策略，详细的列表
可以参见qteasy的手册。

为了确保Operator对象中的DMA策略有合适的参数，我们可以直接传递策略参数到op对象中：

```python
op.set_parameter('t-0', pars=(23, 166, 196))
op.set_parameter('s-0', (0.5,))
op.set_parameter('r-0', (0, 0))
op.info()
```

以上代码为Operator中的三种类型的策略分别设置策略参数，其中't-0'代表timing策略组（择时策略）的第一个策略，s-0和r-0分别表示选股策略组和
风控策略组的第一个策略。他们是自动生成的策略。我们将参数pars=(23, 166, 196)传递给择时策略，其余的策略都使用默认的参数。

最后通过op.info()可以看到Operator对象的信息：

```
OPERATION MODULE INFO:
=========================
Information of the Module
=========================
Total count of SimpleSelecting strategies: 1
the blend type of selecting strategies is 0
Parameters of SimpleSelecting Strategies:
<class 'qteasy.built_in.SelectingAll'> at 0x7f91c3271128
Strategy type: SIMPLE SELECTING
Optimization Tag and opti ranges: 0 [(0, 1)]
Parameter Loaded: <class 'tuple'> (0.5,)
=========================
Total count of timing strategies: 1
The blend type of timing strategies is pos-1
Parameters of timing Strategies:
<class 'qteasy.built_in.TimingDMA'> at 0x7f91c32712b0
Strategy type: QUICK DMA STRATEGY
Optimization Tag and opti ranges: 0 [(10, 250), (10, 250), (10, 250)]
Parameter Loaded: <class 'tuple'> (23, 166, 196)
=========================
Total count of Risk Control strategies: 1
The blend type of Risk Control strategies is add
<class 'qteasy.built_in.RiconNone'> at 0x7f91c32711d0
Strategy type: NONE
Optimization Tag and opti ranges: 0 []
Parameter Loaded: <class 'tuple'> (0, 0)
=========================
```

#### Runing the test session in back-test mode
#### 在回测模式下回测并评价交易策略的性能表现

创建好Operator对象并设置好策略的参数后，策略就已经可以运行了。由于我们使用了内置策略，因此并不需要自己写交易逻辑。

为了验证交易策略的性能，我们需要使用世纪的历史数据对交易策略进行验证，这个验证的过程叫做回测"back-testing"。

使用qteasy，创建好Operator对象后，不管是回测、优化还是实时运行交易策略，都需要用qteast.run()函数，如果要回测策略
的交易结果，需要在run的参数中指明mode=1，以进入回测模式，最简单的回测方式如下：

```python
res = qt.run(op, mode=1, visual=False)
```

如果不需要图形化的输出结果，可以传入参数`visual=False`，这样可以输出纯文本的回测结果如下：

```
qt.run(op, mode=1)

>>>
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

从上面回测结果中可以看出，系统使用了沪深300指数从2016年到2021年共4.2年的历史数据来测试策略，在这段时间内，模拟2016年4月5日投入10万元
投资于沪深300指数，共产生了6次买入信号和6次卖出信号。

到2021年2月1日为止，投资总收益为84.05%，年化收益率为15.63%，而同期沪深300指数本身的涨幅为65%，该策略最终是跑赢了
大盘的。

另外，qteasy还给给出了关于策略表现的几个指标：
如alpha和beta分别是0.026和0.982，而夏普率为0.524。最大回撤发生在2019年4月19日到2020年2月3日，回撤了17.8%，且到了2020年7月6日才
翻盘。

在上面的回测结果中我们给出了参数visual=False，如果我们去掉visual参数，这样还可以得到可视化的回测结果，
默认情况下，回测结果会以图表的形式给出：

![back testing visual result](https://user-images.githubusercontent.com/34448648/123508436-0f058c80-d6a2-11eb-8650-92926e690fae.png)

图表的第一部分列出了与文字输出结果类似的回测相关数据，如回测历史区间起止点和长度、买卖交易次数、收益率、评价指标等
更关键的是下面的图表，通过这个图表可以更清晰地看出这个交易策略的整个运行过程。

第一张图表是回测结果资金曲线图，图中的红色线条就是策略的回测收益率曲线，而蓝色曲线则是作为benchmark的参考股票（此处就是沪深300指数）
曲线的同期收益率，为了方便对比，两条曲线的起点都为0%，并且使用绿色底纹填充参考数据的正收益率部分，用红色填充负收益率部分。

在曲线上有红色的向下箭头和绿色向上箭头，分别代表策略在整个区间上的卖出点和买入点，可以看出，这个策略在回测的最初一段时间内是空仓进场
的，一直到了大约2016年8月的时候产生第一个买入信号，全仓买入沪深300指数，一直持有到2018年2月，除了2017年2/3月有短暂的卖出操作外，一直
持有。接着空仓到2018年12月再次买入，避开了2018年全年的整体下行趋势。

在曲线图上可以看到绿色和白色的条纹状色块，这些色块代表投资的总体仓位，绿色越深则代表多头仓位越高，如果有空头仓位，还会用红色色带表示

曲线图的第二部分是仓位曲线图、第三部分是每日收益图，作为资金曲线图的补充，提供更多的信息。

未来在可视化图表中还会加入更多的回测指标。

前面的回测过程使用的都是默认参数，例如回测区间起止日期等使用的都是默认值，如果要自定义区间起止日期，只需要在qteasy.run()的参数中指定
即可：

```python
res=qt.run(op, 
           asset_pool='000300.SH', 
           asset_type='I',
           invest_start = '20080312')
```

上面的参数指定了回测过程的投资股票池为'000300.SH'，也就是只包含这一只股票（或基金/指数），如果传入一个列表或逗号分隔的字符串，则表示可以
投资于多只不同的股票，如'000300.SH, 000001.SH, 000002.SH'。 asset_type参数表明投资的标的类型为指数，因为某些指数/基金/股票的代码
完全相同，因此必须指定投资标的类型。invest_start为投资回测起始日期，运行上述代码后，得到下面结果：

![back test result 2](https://user-images.githubusercontent.com/34448648/123509564-c56c7000-d6a8-11eb-84cf-9bf5ad15e592.png)

这次回测使用了从2008年开始的共12年的数据，总回报率为440%左右，因为我们从08年的历史高点开始回测的，因此同期的沪深300的收益率只有25%，年化
收益的差异更大，从曲线图上也能看出，策略跑赢了大盘。

#### Optimization of stratepltgies
#### 策略表现的优化

策略的表现与许多因素有关，其中最重要的就是策略的参数。使用较长的均线参数可能会让策略在较长的交易周期中保持盈利，但是可能对短期波动的捕捉却
无能为力，而较短的均线可能可以快速应对股价的变化，但是也有可能导致大量无效的假信号，白白浪费交易成本。因此，通过改变策略的参数来改变或优化
其表现，或者根据投资周期、股票类型、交易波动程度、风险偏好、交易费率高低来找到潜在最优的参数组合，是策略优化的关键。

qteasy提供了简单明了的交易策略优化方法，并且提供了可视化的交易策略优化性能比较工具，有助于帮助找到最优的交易策略参数。

还是以先前

## Strategies and Operations
In this section,  a more in-depth introduction to the Strategies and Operators will reveal more details, introduce more 
parameters and possibilities for users to change the behavier of their test environment.

### Timing Strategies
Genreal introduction to Timing Strategies, what does it do? what kind of data is needed? How does time frequency impacts 
its operation

#### creating long/short position base on historical data
Introduces the first type of usage of Timing strategy. 
Introduces how to create this type of strategy in operator object

#### creating buy/sell signals base on historical data
Introduces how to create buy/sell signal type of strategy in an operator object

#### interally defined timing strategies
Introduces all internally defined timing strategies, including L/S and B/S strategies

#### Simple timing, a faster alternative in some cases
Introduce a faster-running strategy type
Introduce the risk
Introduce the internal timing strategies that can be operated on simple timing strategy

### Selecting Strategies
Introduce the meaning of Selecting Strategies

### Define your own strategies
Introduces how to create a self-defined strategy

### Combination of Strategies
Introduces strategy blender, and how they are blended in different case
Introduces all blending parameters

## Historical Data
Introduce to the HistoryPanel object

### Operations of Historical data -- HistoryPanel()

### Converting of HistoryPanel to other forms

## Back-test of Strategies

### Back-test methods
Introduces all kinds of back-testing methods

### Set up investment plan with Cashplan() objects
Introduces all kind of usages of CashPlan() objects
Cashplan sets up how the cash investment is planned during the backtesting of strategies

a Cashplan object can be simply created by: 

```python
In [52]: cp=qt.CashPlan(dates='2010-01-01', amounts=100000)                                                                                

In [53]: cp                                                                                                                                
Out[53]: 
            amount
2010-01-01  100000
```
a cashplan with multiple cash investments can be also created by passing list or string into __init__() function of CashPlan():

```python
cp=qt.CashPlan(dates='2010-01-01, 2011-01-01', amounts=[100000, 100000])
```

### Evaluation of back-test results
Back test result can be evaluation in multiple ways:
Use parameter `eval='FV, alpha'`to control the evaluation methods
#### FV

#### alpha

### visualization of batk-test results
visualization allows a better comprehension of the results

### back-test logs
Back-test logs records each and every operation steps

## Optimization of Strategies
Optimization means to find the parameter that will possibly create the best output in a certain historical periods

### using parameter searching algorithms
There are multiple parameter searching methods

### 