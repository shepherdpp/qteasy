# coding=utf-8

import numpy as np
import numba
from talib import EMA, SMA, MACD

# TODO: 以talib为基础创建一个金融函数库

@numba.jit(nopython=True, target='cpu', parallel=True)
def ema(arr, span: int = None):
    """基于numpy的高速指数移动平均值计算.

    input：
        :param arr: 1-D ndarray, 输入数据，一维矩阵
        :param span: int, optional, 1 < span, 跨度
    output：=====
        :return: 1-D ndarray; 输入数据的指数平滑移动平均值
    """

    return EMA(arr, span)

def ma(arr, window: int > 1):
    """Simple Moving Average
       简单的移动平均值计算

    input：
        :param window: type: int, 1 < window, 时间滑动窗口
        :param arr: type: object np.ndarray: 输入数据，一维矩阵
    return：
        :return: ndarray, 完成计算的移动平均序列
    """

    return SMA(arr, window)

def macd(arr, short:int, long:int, change:int):
    """MACD计算

    input
        :param arr:
        :param short:
        :param long:
        :param change:
    :return:
        type:
    """

    return MACD(arr, short, long, change)