# coding=utf-8
# ======================================
# File:     akfuncs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-09-11
# Desc:
#   Interfaces to akshare data api.
# ======================================


from qteasy.__init__ import logger_core, QT_CONFIG

from qteasy.utilfuncs import (
    retry,
)

import akshare as ak

ERRORS_TO_CHECK_ON_RETRY = Exception

EXTRA_RETRY_API = [

]


# tsfuncs interface function, call this function to extract data
def acquire_data(api_name, **kwargs):
    """ DataSource模块的接口函数，根据根据table的内容调用相应的akshare API下载数据，并以DataFrame的形式返回数据"""
    data_download_retry_count = QT_CONFIG.hist_dnld_retry_cnt
    data_download_retry_wait = QT_CONFIG.hist_dnld_retry_wait
    data_download_retry_backoff = QT_CONFIG.hist_dnld_backoff

    if api_name in EXTRA_RETRY_API:
        data_download_retry_count += 3

    retry_decorator = retry(
            exception_to_check=ERRORS_TO_CHECK_ON_RETRY,
            mute=True,
            tries=data_download_retry_count,
            delay=data_download_retry_wait,
            backoff=data_download_retry_backoff,
            logger=logger_core,
    )
    func = globals()[api_name]
    decorated_func = retry_decorator(func)
    res = decorated_func(**kwargs)
    return res


def stock_daily(qt_code, start, end):
    """获取股票日线数据"""
    raise NotImplementedError


def stock_weekly(qt_code, start, end):
    """获取股票周线数据"""
    raise NotImplementedError


def stock_monthly(qt_code, start, end):
    """获取股票月线数据"""
    raise NotImplementedError


def index_daily(qt_code, start, end):
    """获取指数日线数据"""
    raise NotImplementedError


def index_weekly(qt_code, start, end):
    """获取指数周线数据"""
    raise NotImplementedError


def realtime_bars(qt_code):
    """获取实时K线数据"""
    raise NotImplementedError


def realtime_quotes(qt_code):
    """获取实时行情数据"""
    raise NotImplementedError
