# coding=utf-8
# ======================================
# File:     errors.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-03-06
# Desc:
#   Definition of errors in qteasy
# ======================================

import os

'''
This file is not final, it is just a placeholder for future development.
Definition of errors in qteasy, here at least following types of errors are defined:

- QTEasyError: Base class for exceptions in qteasy
- DataSourceConnectionError: Error raised when connection to data source failed
- BrokerConnectionError: Error raised when connection to broker failed
- StrategyError: Error raised when strategy execution failed
- DataError: Error raised when data processing failed
- And more ...
'''


class QTEasyError(Exception):
    """Base class for exceptions in qteasy"""
    pass


class DataSourceConnectionError(QTEasyError):
    """Error raised when connection to data source failed"""
    pass


class BrokerConnectionError(QTEasyError):
    """Error raised when connection to broker failed"""
    pass


class StrategyError(QTEasyError):
    """Error raised when strategy execution failed"""
    pass


class DataError(QTEasyError):
    """Error raised when data processing failed"""
    pass
