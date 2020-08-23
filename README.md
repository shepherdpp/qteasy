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
- optimization
- looping

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
