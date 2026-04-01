启动QTEASY
==============

启动qteasy的配置信息:

.. autofunction:: qteasy.run

.. autofunction:: qteasy.info


运行模式与常量速查
------------------

qteasy 使用一组全局常量表示运行模式（实盘/回测/优化/预测）。你可以在调用 ``qt.run`` 前后通过
``qt.configure(mode=...)`` 或在 ``qt.run(op, mode=...)`` 中临时覆盖。

示例（常量值为稳定输出）：:

    >>> import qteasy as qt
    >>> qt.LIVE_MODE, qt.BACKTEST_MODE, qt.OPTIMIZE_MODE, qt.PREDICT_MODE
    (0, 1, 2, 3)

日志与根目录路径常量（值受配置影响，尤其是日志路径支持运行时热更新）：:

    >>> import qteasy as qt
    >>> isinstance(qt.QT_ROOT_PATH, str)
    True
    >>> isinstance(qt.QT_SYS_LOG_PATH, str) and isinstance(qt.QT_TRADE_LOG_PATH, str)
    True
