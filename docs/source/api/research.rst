qteasy.research （因子研究模块）
================================

``qteasy.research`` 提供**模块级**因子研究函数（截面 IC、分位组合、多空收益等）。

这些 API：

- **不是** Backtester：不计算交割、费用、MOQ 或正式交易报告；
- **不**挂在 ``HistoryPanel`` 方法上（请 ``from qteasy.research import ...``）；
- **不**内置 Newey–West / Fama–MacBeth（发表级推断请导出到 pandas / statsmodels，见教程 2.5 §11）；
- ``factor_ic`` **不会**隐式前瞻：收益列须由调用方事先用 ``shift`` / ``pct_change`` 等造好。

导入示例::

    from qteasy.research import (
        factor_ic,
        factor_ic_summary,
        quantile_portfolio,
        long_short_return,
    )

可运行合成示例见仓库 ``examples/historypanel_research_factor_workflow.py``。
与面板级时序相关矩阵 （``HistoryPanel.corr`` / ``cov``）的语义对照见 :doc:`HistoryPanel <HistoryPanel>`。


截面 IC
-------

.. autofunction:: qteasy.research.factor_ic

.. autofunction:: qteasy.research.factor_ic_summary


分位组合与多空
-------------

.. autofunction:: qteasy.research.quantile_portfolio

.. autofunction:: qteasy.research.long_short_return
