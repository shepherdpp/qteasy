## qteasy
### a python-based fast quantitative analysis module for investment strategy creating, looping and optimizing

Author: **Jackie PENG**

email: *jackie_pengzhao@163.com* 

Project created on: 2019, July, 16

## Installation and dependencies
This project requires and depends on following packages:
- *`pandas` version 0.25*
- *`numpy` version 0.19*
- *`TA-lib` version 0.4*
- *`tushare` version 1.24.1*
- *`matplotlib.mplfinance` version 0.12*

## Introductions

This project is aiming at a fast quantitative investment package for python, with following functions:

1. Historical and real time data downloading and management, visualization
2. Investment strategy creation, backlooping, adjusting, assessment and optimization
3. Live stock trading: trading operation submission, withdrawal, status checking and feedback reporting

The target of this module is to be a very fast and highly effective system that processes big data for quants

## Contents and Tutorials

- basic usage
- strategy creation
- looping
- optimization

## Basic usage
The convensional way of importing this package is following:

```python
import qteasy as qt
```
Then the classes and functions can be used:

```python
ht = qt.HistoryPanel()
op = qt.Operator()
```
### Load and visualize Stock prices
With `qteasy`, historical stock price data can be easily loaded and displayed, with a series of functions that helps visualizing price data. for example:
```python
qt.ohlt('000300.SZ', start='2020-03-01')

```
![image of ohlc plot]
(https://user-images.githubusercontent.com/34448648/91590745-648fe080-e98e-11ea-9b73-369e9dd78990.png)
### Creating Strategies


### Creating Operators