HistoryPanel 类
==================

历史数据类 HistoryPanel 及相关辅助函数。

.. autoclass:: qteasy.HistoryPanel
    :members:

.. autofunction:: qteasy.get_history_data

.. autofunction:: qteasy.stack_dataframes

.. autofunction:: qteasy.dataframe_to_hp


基础统计与聚合
----------------

以下方法在 HistoryPanel 的三维数据上提供类似 pandas 的统计功能：

.. automethod:: qteasy.HistoryPanel.describe

.. automethod:: qteasy.HistoryPanel.mean

.. automethod:: qteasy.HistoryPanel.std

.. automethod:: qteasy.HistoryPanel.min

.. automethod:: qteasy.HistoryPanel.max


滚动窗口
----------

.. automethod:: qteasy.HistoryPanel.rolling

.. autoclass:: qteasy.history.HistoryPanelRolling
    :members:


收益与风险指标
----------------

.. automethod:: qteasy.HistoryPanel.returns

.. automethod:: qteasy.HistoryPanel.volatility

.. automethod:: qteasy.HistoryPanel.alpha_beta


K 线与技术指标
----------------

.. autoattribute:: qteasy.HistoryPanel.kline

.. automethod:: qteasy.HistoryPanel.apply_ta

.. automethod:: qteasy.HistoryPanel.candle_pattern
