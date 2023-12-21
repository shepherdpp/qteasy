内置交易策略
===================

获取内置交易策略
-----------------------

.. autofunction:: qteasy.built_ins

.. autofunction:: qteasy.built_in_list

.. autofunction:: qteasy.built_in_strategies

所有内置交易策略
-----------------------

下面是所有的内置交易策略

简单选股策略
------------

根据历史数据选股

.. autofunction:: qteasy.built_in.SelectingAll

.. autofunction:: qteasy.built_in.SelectingNone

.. autofunction:: qteasy.built_in.SelectingRandom

.. autofunction:: qteasy.built_in.SelectingAvgIndicator

.. autofunction:: qteasy.built_in.SelectingNDayLast

.. autofunction:: qteasy.built_in.SelectingNDayAvg

.. autofunction:: qteasy.built_in.SelectingNDayChange

.. autofunction:: qteasy.built_in.SelectingNDayRateChange

.. autofunction:: qteasy.built_in.SelectingNDayVolatility

.. autofunction:: qteasy.built_in.SignalNone

.. autofunction:: qteasy.built_in.SellRate

.. autofunction:: qteasy.built_in.BuyRate

简单择时策略
------------

.. autofunction:: qteasy.built_in.TimingLong

.. autofunction:: qteasy.built_in.TimingShort

.. autofunction:: qteasy.built_in.TimingZero

基于均线指标的择时策略
----------------------

下面的选股策略都基于股价均线指标来判定买入卖出

.. autofunction:: qteasy.built_in.DMA

.. autofunction:: qteasy.built_in.MACD

.. autofunction:: qteasy.built_in.TRIX

.. autofunction:: qteasy.built_in.Crossline

.. autofunction:: qteasy.built_in.CDL

.. autofunction:: qteasy.built_in.SoftBBand

.. autofunction:: qteasy.built_in.BBand


基于单均线穿越的择时策略
------------------------

以下所有内置策略都需要安装`TA-Lib`

下面的选股策略都基于股价是否上穿/下穿均线来判定买入卖出

.. autofunction:: qteasy.built_in.SCRSSMA

.. autofunction:: qteasy.built_in.SCRSDEMA

.. autofunction:: qteasy.built_in.SCRSEMA

.. autofunction:: qteasy.built_in.SCRSHT

.. autofunction:: qteasy.built_in.SCRSKAMA

.. autofunction:: qteasy.built_in.SCRSMAMA

.. autofunction:: qteasy.built_in.SCRST3

.. autofunction:: qteasy.built_in.SCRSTEMA

.. autofunction:: qteasy.built_in.SCRSTRIMA

.. autofunction:: qteasy.built_in.SCRSWMA


基于双均线穿越的择时策略
------------------------

下面的选股策略都基于两根（一快一慢）均线是否交叉来判定买入卖出

.. autofunction:: qteasy.built_in.DCRSSMA

.. autofunction:: qteasy.built_in.DCRSDEMA

.. autofunction:: qteasy.built_in.DCRSEMA

.. autofunction:: qteasy.built_in.DCRSKAMA

.. autofunction:: qteasy.built_in.DCRSMAMA

.. autofunction:: qteasy.built_in.DCRST3

.. autofunction:: qteasy.built_in.DCRSTEMA

.. autofunction:: qteasy.built_in.DCRSTRIMA

.. autofunction:: qteasy.built_in.DCRSWMA

基于均线斜率的择时策略
----------------------

下面的选股策略都基于均线的斜率来判定买入卖出

.. autofunction:: qteasy.built_in.SLPSMA

.. autofunction:: qteasy.built_in.SLPDEMA

.. autofunction:: qteasy.built_in.SLPEMA

.. autofunction:: qteasy.built_in.SLPHT

.. autofunction:: qteasy.built_in.SLPKAMA

.. autofunction:: qteasy.built_in.SLPMAMA

.. autofunction:: qteasy.built_in.SLPT3

.. autofunction:: qteasy.built_in.SLPTEMA

.. autofunction:: qteasy.built_in.SLPTRIMA

.. autofunction:: qteasy.built_in.SLPWMA

.. autofunction:: qteasy.built_in.SAREXT

基于其他技术指标的择时策略
----------------------------

下面的选股策略都基于均线的斜率来判定买入卖出

.. autofunction:: qteasy.built_in.ADX

.. autofunction:: qteasy.built_in.APO

.. autofunction:: qteasy.built_in.AROON

.. autofunction:: qteasy.built_in.CMO

.. autofunction:: qteasy.built_in.MACDEXT

.. autofunction:: qteasy.built_in.MFI

.. autofunction:: qteasy.built_in.DI

.. autofunction:: qteasy.built_in.DM

.. autofunction:: qteasy.built_in.MOM

.. autofunction:: qteasy.built_in.PPO

.. autofunction:: qteasy.built_in.RSI

.. autofunction:: qteasy.built_in.STOCH

.. autofunction:: qteasy.built_in.STOCHF

.. autofunction:: qteasy.built_in.STOCHRSI

.. autofunction:: qteasy.built_in.ULTOSC

.. autofunction:: qteasy.built_in.WILLR

.. autofunction:: qteasy.built_in.AD

.. autofunction:: qteasy.built_in.ADOSC

.. autofunction:: qteasy.built_in.OBV

