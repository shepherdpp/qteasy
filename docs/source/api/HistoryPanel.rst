HistoryPanel 类
==================

历史数据类 HistoryPanel 及相关辅助函数。

HistoryPanel 数据结构与切片
---------------------------

HistoryPanel 本质上是一个三维 ``numpy.ndarray``，三个轴分别表示：

- axis 0 / levels: 标的维度，每一层对应一只股票或一个指数，标签列表为 ``shares``；
- axis 1 / rows: 时间维度，每一行对应一个时间点，标签列表为 ``hdates``；
- axis 2 / columns: 历史数据类型维度，每一列对应一种数据类型，标签列表为 ``htypes``。

借助这三个轴标签，可以通过方括号 ``[]`` 对 HistoryPanel 进行灵活切片，基本规则为
``[htype_slicer, share_slicer, date_slicer]``，举例如下（只展示典型场景，更多细节参考
示例与教程文档）::

    hp['close']                       # 所有标的的收盘价
    hp['close,open,high']            # 所有标的的多种价量数据
    hp[:, '000300.SH']               # 单一标的的全部历史数据
    hp['close:high', ['000300.SH', '000500.SH'], '20100101:20101231']
                                     # 多标的、数据类型与时间区间联合切片


.. autoclass:: qteasy.HistoryPanel
    :members:


HistoryPanel 对象提供了常用的金融数据统计与聚合方法，包括数据的描述性统计、滚动窗口计算、收益与风险指标计算，以及 K 线与技术指标计算等，具体如下：

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

使用滚动窗口方法可以在 HistoryPanel 的时间维度上进行滑动计算，支持常见的滚动平均、滚动标准差等操作：

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


qteasy级别的历史数据处理函数
-----------------------------------------------

qteasy 还提供了若干独立于 HistoryPanel 类的函数，支持更灵活的历史数据处理与分析：

.. autofunction:: qteasy.get_history_data

.. autofunction:: qteasy.stack_dataframes