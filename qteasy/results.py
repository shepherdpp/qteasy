# coding=utf-8
# ======================================
# File:     results.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-05-02
# Desc:
#   Classes that handles the strategy
# backtest and optimization results.
# ======================================

import numpy as np
import pandas as pd


class BacktestResult():
    """ Class that handles the results of a backtest.

    """

    def __init__(self, dates, shares, cashes: np.ndarray, fees: np.ndarray, values:np.ndarray, amounts: np.ndarray):
        """ 初始化result对象

        Parameters
        ----------
        dates: np.ndarray or list
            交易日期，记录每一交易回合的交易日期时间
        shares: np.ndarray or list
            资产名称，整个交易目标组合的资产名称/资产编码
        cashes: np.ndarray
            现金变动，记录每一交易回合的现金金额变化量，>0表示现金增加，<0表示现金减少
        fees: np.ndarray
            交易费用，记录每一交易回合产生的交易费用
        values：np.ndarray
            资产总值，记录每一交易回合的资产总值
        amounts: np.ndarray
            资产数量，记录每一交易回合的资产数量
        """
        # 生成回测结果的最主要内容——回测历史记录清单
        self.value_history = value_history = pd.DataFrame(amounts, index=dates, columns=shares)
        # 填充标量计算结果
        value_history['cash'] = cashes
        value_history['fee'] = fees
        value_history['value'] = values
        # 添加其他的属性，用于记录回测结果的其他信息，属性暂时为空
        raise NotImplementedError

    def create_operation_log(self, operation_log):
        """ 生成交易记录清单

        Parameters
        ----------
        operation_log: pd.DataFrame
            交易记录清单，记录每一笔交易的交易时间、资产名称、交易数量、交易价格、交易费用
        """
        raise NotImplementedError

    def create_trade_log(self, trade_log):
        """ 生成交易日志清单

        Parameters
        ----------
        trade_log: pd.DataFrame
            交易日志清单，记录每一笔交易的交易时间、资产名称、交易数量、交易价格
        """
        raise NotImplementedError

    def create_complete_history(self, complete_history):
        """ 生成完整历史记录清单

        Parameters
        ----------
        complete_history: pd.DataFrame
            完整历史记录清单，记录每一交易回合的交易日期时间、资产名称、资产数量、资产价格、现金金额、交易费用、资产总值
        """
        raise NotImplementedError

    def print_report(self):
        """ 打印回测报告

        """
        raise NotImplementedError

    def plot_results(self):
        """ 绘制回测结果图

        """
        raise NotImplementedError

    def save_results(self):
        """ 保存回测结果

        """
        raise NotImplementedError
