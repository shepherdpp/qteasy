## qteasy
### a python-based fast quantitative analysis module for investment strategy creating, looping and optimizing
### 一个基于Python的量化投资工具包，用于投资策略的创建、快速回测以及优化

Author: **Jackie PENG**

email: *jackie_pengzhao@163.com* 

Project created on: 2019, July, 16

## Installation and dependencies 安装及依赖包
This project requires and depends on following packages:
- *`pandas` version 0.25*
- *`numpy` version 0.19*
- *`TA-lib` version 0.4*
- *`tushare` version 1.24.1*
- *`matplotlib.mplfinance` version 0.12*

## Introductions 介绍

This project is aiming at a fast quantitative investment package for python, with following functions:

1. Historical and real time data downloading and management, visualization
2. Investment strategy creation, backlooping, adjusting, assessment and optimization
3. Live stock trading: trading operation submission, withdrawal, status checking and feedback reporting

The target of this module is to be a very fast and highly effective system that processes big data for quants

## Contents and Tutorials 内容及教程

- basic usage 基本使用方法
- strategy creation 投资策略的创建
- Back-test of strategies 投资策略的回测
- Strategy Optimization 投资策略的优化

## Basic usage: A 10-min introduction to qteasy 基本使用方法，10分钟熟悉qteasy的使用
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
```python
qt.ohlt('000300.SZ', start='2020-03-01')

```
the ohlc chart of stock 000300 will be displayed:

![image of ohlc plot](https://user-images.githubusercontent.com/34448648/91590745-648fe080-e98e-11ea-9b73-369e9dd78990.png)

### Create and running of investment strategy sessions

In this section, a short and simple example will be given for the readers to go through the process of creating a 
strategy, testing it throught back-testing function, and searching for parameters that allows the strategy to provide 
the best output with given historical data.

There are multiple internally preset strategies such as crossline timing strategy or DMA timing strategy provided in
 qteasy, a strategy should be created with an Operator object, the Operator is the container of strategies, and provides
 multiple methods to utilize and operate on these strategies.
 
 An Opertor with a DMA strategy can be created like this:
 
 ```python
op = qt.Operator(timing_types='DMA')
```
 
#### Timing strategy Example: Cross-Line strategy

In this section,  a cross-line timing strategy will be created, as a demonstration of how a strategy can be created
through internally defined strategies, and how to set up the strategy with a Operator() object.

#### Control strategy with parameters

In this section,  the parameters of the strategy will be set as an example, and different effects will be introduced

#### Control operation test with Context() object

In this subsection, context() object will be introduce to show how testing environmental changes its behavior while
context paramters are changed. 

#### Runing the test session in back-test mode

In this subsection, the test session will be performed in hack-test mode, to show how back test result is generated 
for a certain strategy.

#### Optimization of stratepltgies

In this subsection, we will demostrate optimizaiton process: run the session in optimization mode, and find out best 
performers within the parameter space.

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