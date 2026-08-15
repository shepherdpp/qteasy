# coding=utf-8
# ======================================
# File:     __init__.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-08-15
# Desc:
#   qteasy.research：因子研究模块级 API（非 Backtester）。
# ======================================

from qteasy.research.factor_stats import factor_ic, factor_ic_summary

__all__ = [
    'factor_ic',
    'factor_ic_summary',
]
