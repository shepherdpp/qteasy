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
``[htype_slicer, share_slicer, date_slicer]``；**省略维度时**与单段写法（如 ``hp['close']``）仍返回 **子 HistoryPanel**（带轴标签），裸矩阵请用 ``.values`` / ``.to_numpy()``。

**时间轴（第三段）** 还支持：单个 ``pandas.Timestamp``、时间标签列表、长度 ``L = len(hdates)`` 的一维 ``bool`` 列表或 ``numpy`` 一维 ``bool`` 数组；与只读属性 ``hp.loc[key]`` 等价于 ``hp[:, :, key]``。格点级 ``(M, L, N)`` 布尔掩码不属于 ``loc`` / 第三轴索引语义，请用 :meth:`~qteasy.HistoryPanel.where`。

典型写法示例::

    hp['close']                       # 所有标的的收盘价
    hp['close,open,high']            # 所有标的的多种价量数据
    hp[:, '000300.SH']               # 单一标的的全部历史数据
    hp['close:high', ['000300.SH', '000500.SH'], '20100101:20101231']
                                     # 多标的、数据类型与时间区间联合切片
    hp.loc[0:5]                       # 与 hp[:, :, 0:5] 等价，按时间轴截取


.. autoclass:: qteasy.HistoryPanel
    :members:
    :special-members: __getitem__, __setitem__, __getattr__, __lt__, __le__, __gt__, __ge__, __eq__, __ne__


HistoryPanel 对象提供了常用的金融数据统计与聚合方法，包括数据的描述性统计、滚动窗口计算、收益与风险指标计算，以及 K 线与技术指标计算等，具体如下：

基础统计与聚合
----------------

以下方法在 HistoryPanel 的三维数据上提供类似 pandas 的统计功能：

.. automethod:: qteasy.HistoryPanel.describe

.. automethod:: qteasy.HistoryPanel.mean

.. automethod:: qteasy.HistoryPanel.std

.. automethod:: qteasy.HistoryPanel.min

.. automethod:: qteasy.HistoryPanel.max


研究与掩码（``where``）
----------------------

将任意可广播条件规整为与 ``values`` 同形的 ``bool`` 数组，供后续研究 API 的 ``mask=`` 参数使用（如累计收益、归一化、组合聚合等）。二维 ``(M, L)`` 条件会沿 htype 轴复制到 ``(M, L, N)``；详见方法 docstring 与教程「使用 HistoryPanel 操作和分析历史数据」。

.. automethod:: qteasy.HistoryPanel.where

以下为与教程互补的稍长示例（不依赖网络；可与 docstring 中 doctest 对照）：

.. code-block:: python

   import numpy as np
   import pandas as pd
   from qteasy import HistoryPanel

   # 最小面板：M=2, L=3, N=4
   hp = HistoryPanel(
       np.arange(24, dtype=float).reshape(2, 3, 4),
       levels=['A', 'B'],
       rows=pd.date_range('2020-01-01', periods=3),
       columns=['a', 'b', 'c', 'd'],
   )
   # Event window on time axis: last row True for all shares and htypes
   M, L, N = hp.shape
   event_ml = np.zeros((M, L), dtype=bool)
   event_ml[:, -1] = True
   mask_event = hp.where(event_ml)
   assert mask_event[:, -1, :].all() and not mask_event[:, 0, :].any()

阶段四及以后，计划支持将 ``mask = hp.where(...)`` 直接传入 ``cum_return``、``normalize`` 等；发布前请以 docstring 与教程为准。

列属性访问、比较与 ``loc``（与 pandas 的差异）
----------------------------------------------

- **属性**：合法标识符列名可用 ``hp.close``（只读），等价 ``hp['close']``；含 ``|`` 等非法标识符的列名、以及未知名仍须用 ``hp['...']``。赋值请统一 ``hp['col'] = ...``。已有方法 / 描述符（如 ``where``、``values``）与同名列冲突时，点号仍解析为 API，列请用方括号。
- **比较**：``hp > 0``、``hp['close'] > hp['open']`` 等返回 **``numpy.ndarray``（bool）**，**不**返回 ``HistoryPanel``；可与 ``hp.where(...)`` 衔接。两侧均为面板时须 ``shares``、``hdates`` 一致；``htypes`` 须一致，**或**两侧均为单列切片（如两列比较）。
- **``loc``**：``hp.loc[k]`` 等价 ``hp[:, :, k]``，仅沿 **时间轴（hdates）** 筛选；**不**接受 ``where`` 的 ``(M, L, N)`` 布尔立方，格点掩码请 ``where`` + ``mask=``。

.. autoattribute:: qteasy.HistoryPanel.loc

简短示例（可与 :meth:`~qteasy.HistoryPanel.where` 联用）：

.. code-block:: python

   # 假设 hp 已含 'close' 列
   # mask = hp.where(hp.close > 100.0)           # 比较结果为 bool ndarray，再规整为 (M,L,N)
   # sub = hp.loc[0:20]                          # 等价 hp[:, :, 0:20]，按时间轴截取
   # L = len(hp.hdates)
   # sub2 = hp.loc[[True]*3 + [False]*(L - 3)]   # 一维 bool 长度须等于 L

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