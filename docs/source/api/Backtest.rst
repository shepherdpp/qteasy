Backtester 策略回测器
===================================

Backtester类用于对operator对象进行回测操作。

本类的属性包括回测计算中所需的所有参数，包括回测过程中产生的结果数据，这些结果数据以ndarray的形式
在对象的生命周期内长期保存，并可以反复刷新。

这个类只有在operator对象被创建之后才能被实例化，因为Backtester类需要依赖operator对象来生成交易
信号和执行交易。典型用法如下：
```
    operator = Operator( ... )  # 创建Operator对象
    backtested = Operator.backtest( signal_count=100, share_count=10, **kwargs)  # 创建Backtester对象
    # get backtest raw results:
    backtested.cash_investment_array
    backtested.own_cashes
    ...
    # get backtest results as DataFrame:
    result_df = backtested.value_records()
    trade_log_df = backtested.trade_logs()
    trade_summary_df = backtested.trade_summary()
```

.. autoclass:: qteasy.backtest.Backtester
    :members:

