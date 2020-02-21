# coding=utf-8

import numpy as np
import numba

@numba.jit(nopython=True, target='cpu', parallel=True)
def ema(arr, span: int = None, alpha: float = None):
    """基于numpy的高速指数移动平均值计算.

    input：
        :param arr: 1-D ndarray, 输入数据，一维矩阵
        :param span: int, optional, 1 < span, 跨度
        :param alpha: float, optional, 0 < alpha < 1, 数据衰减系数
    output：=====
        :return: 1-D ndarray; 输入数据的指数平滑移动平均值
    """
    if alpha is None:
        alpha = 2 / (span + 1.0)
    alpha_rev = 1 - alpha
    n = arr.shape[0]
    pows = alpha_rev ** (np.arange(n + 1))
    scale_arr = 1 / pows[:-1]
    offset = arr[0] * pows[1:]
    pw0 = alpha * alpha_rev ** (n - 1)
    mult = arr * pw0 * scale_arr
    cumsums = mult.cumsum()
    return offset + cumsums * scale_arr[::-1]


@numba.jit(nopython=True)
def ma(arr, window: int):
    """Fast moving average calculation based on NumPy
       基于numpy的高速移动平均值计算

    input：
        :param window: type: int, 1 < window, 时间滑动窗口
        :param arr: type: object np.ndarray: 输入数据，一维矩阵
    return：
        :return: ndarray, 完成计算的移动平均序列
    """
    arr_ = arr.cumsum()
    arr_r = np.roll(arr_, window)
    arr_r[:window - 1] = np.nan
    arr_r[window - 1] = 0
    return (arr_ - arr_r) / window

