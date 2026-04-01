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

可将 ``mask = hp.where(...)`` 直接传入 :meth:`~qteasy.HistoryPanel.cum_return` 与 :meth:`~qteasy.HistoryPanel.normalize` 的 ``mask=`` 参数（广播规则与 ``where`` 一致）。

列属性访问、比较与 ``loc``（与 pandas 的差异）
----------------------------------------------

- **属性**：合法标识符列名可用 ``hp.close``（只读），等价 ``hp['close']``；含 ``|`` 等非法标识符的列名、以及未知名仍须用 ``hp['...']``。赋值请统一 ``hp['col'] = ...``。已有方法 / 描述符（如 ``where``、``values``）与同名列冲突时，点号仍解析为 API，列请用方括号。
- **比较**：``hp > 0``、``hp['close'] > hp['open']`` 等返回 **``numpy.ndarray``（bool）**，**不**返回 ``HistoryPanel``；可与 ``hp.where(...)`` 衔接。两侧均为面板时须 ``shares``、``hdates`` 一致；``htypes`` 须一致，**或**两侧均为单列切片（如两列比较）。
- **``loc``**：``hp.loc[k]`` 等价 ``hp[:, :, k]``，仅沿 **时间轴（hdates）** 筛选；**不**接受 ``where`` 的 ``(M, L, N)`` 布尔立方，格点掩码请 ``where`` + ``mask=``。
- **算术与拷贝**：

  - ``hp + 1``、``hp * arr`` 等算术运算会 **返回新 ``HistoryPanel``**，不修改原对象。
  - ``hp += 1``、``hp *= arr`` 等 **就地运算符**会显式修改原对象。
  - ``hp.copy(deep=True)``（默认）返回深拷贝，修改副本不影响原对象；``hp.copy(deep=False)`` 共享底层数组，修改副本会同步影响原对象。

与 ``plot`` 的衔接：用 (M,L) mask 做高亮
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在研究场景中，事件日/信号/可交易池常见输出为二维布尔矩阵 ``mask_ml``，形状为 ``(M, L)``（标的数 × 时间长度）。
`HistoryPanel.plot()` 的 ``highlight`` 支持把该二维 mask 映射到当前图形中的高亮点：

- **子集 mask**：若 ``mask_ml.shape == (M_plot, L)``，其中 ``M_plot`` 为本次 ``plot(shares=...)`` 选中的 share 数，则按绘图 share 顺序对应；
- **全量 mask**：若 ``mask_ml.shape == (M_all, L)``（``M_all == len(hp.shares)``），则按 **share 名**抽取当前绘图子集（禁止按位置静默截断）；\n
- **overlay**：当 ``layout='overlay'`` 且两标的叠加时，默认 **primary-only** 显示高亮（与 Plotly highlight 既有语义一致）。\n

示例::

    import numpy as np
    hp = ...  # 已构造好的 HistoryPanel
    M, L, N = hp.shape
    mask_ml = np.zeros((M, L), dtype=bool)
    mask_ml[:, -1] = True
    fig = hp.plot(highlight={'condition': mask_ml})

.. autoattribute:: qteasy.HistoryPanel.loc

列级 DSL：assign
-----------------

``assign`` 提供类似 pandas 的列级 DSL，可以一次性派生或更新多列，支持在单次调用中基于已有列或刚新增的列构造新因子；支持返回新面板或在原面板上原地扩列。

.. automethod:: qteasy.HistoryPanel.assign

简短示例（可与 :meth:`~qteasy.HistoryPanel.where` 联用）：

.. code-block:: python

   # 假设 hp 已含 'close' 列
   # mask = hp.where(hp.close > 100.0)           # 比较结果为 bool ndarray，再规整为 (M,L,N)
   # sub = hp.loc[0:20]                          # 等价 hp[:, :, 0:20]，按时间轴截取
   # L = len(hp.hdates)
   # sub2 = hp.loc[[True]*3 + [False]*(L - 3)]   # 一维 bool 长度须等于 L

横截面与标准化：rank / zscore
----------------------------

``rank`` 与 ``zscore`` 用于轻量因子研究中的“逐日截面排名/标准化”与“逐股时序滚动标准化”。
``zscore`` 通过 ``method`` 显式区分两种语义：

- ``method='cs'``：固定日期，在 share 维做截面标准化；
- ``method='ts'``：固定 share，在时间轴上做滚动标准化（需要 ``window``）。

.. automethod:: qteasy.HistoryPanel.rank

.. automethod:: qteasy.HistoryPanel.zscore

对齐与重采样：align_to / resample
-------------------------------

当你需要对两个 ``HistoryPanel`` 做逐元素运算（例如相除、相减、相关性等）时，若两者的 ``shares`` 或 ``hdates``
不一致，NumPy 广播可能产生**静默错行**（silent misalignment）。因此本项目提供显式对齐入口：

- :meth:`~qteasy.HistoryPanel.align_to`：按标签对齐 ``shares`` 与 ``hdates``，支持 ``join='inner'|'outer'``，缺失处填 ``fill_value``；
- :meth:`~qteasy.HistoryPanel.resample`：沿时间轴重采样，**必须显式**提供 ``agg=``（覆盖全部 ``htypes``），避免聚合语义不明导致“看似成功但结果不可解释”。\n

.. automethod:: qteasy.HistoryPanel.align_to

.. automethod:: qteasy.HistoryPanel.resample

滚动窗口
----------

使用滚动窗口方法可以在 HistoryPanel 的时间维度上进行滑动计算，支持常见的滚动平均、滚动标准差等操作：

.. automethod:: qteasy.HistoryPanel.rolling

.. autoclass:: qteasy.history.HistoryPanelRolling
    :members:


收益与风险指标
----------------

.. automethod:: qteasy.HistoryPanel.returns

.. automethod:: qteasy.HistoryPanel.cum_return

.. automethod:: qteasy.HistoryPanel.normalize

.. automethod:: qteasy.HistoryPanel.portfolio

.. automethod:: qteasy.HistoryPanel.volatility

.. automethod:: qteasy.HistoryPanel.alpha_beta


K 线与技术指标
----------------

第一入口：research_preset
~~~~~~~~~~~~~~~~~~~~~~~~

``research_preset`` 用于快速拼出「可直接 plot 的常用列集合」（例如 OHLCV + MACD + MA），避免在绘图阶段隐式计算指标。缺少输入列时会抛出英文 ``ValueError`` 并给出缺列提示。

.. automethod:: qteasy.HistoryPanel.research_preset

.. autoattribute:: qteasy.HistoryPanel.kline

.. automethod:: qteasy.HistoryPanel.apply_ta

.. automethod:: qteasy.HistoryPanel.candle_pattern


qteasy级别的历史数据处理函数
-----------------------------------------------

qteasy 还提供了若干独立于 HistoryPanel 类的函数，支持更灵活的历史数据处理与分析：

.. autofunction:: qteasy.get_history_data

.. autofunction:: qteasy.stack_dataframes