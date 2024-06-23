内置交易策略
===================

qteasy提供超过70种内置交易策略，所有的交易策略都可以直接使用，通过修改这些交易策略的参数，可以很容易地实现不同的个性化效果。

qteasy所有的内置交易策略都有完整的说明文档，提供了交易策略的详细说明，参数说明，以及默认参数值。每一个qteasy内置交易策略都有一个ID，通过这个唯一的ID
用户可以容易地获取这个交易策略，查看说明文档，或者直接在创建Operator对象时使用这个交易策略。

获取内置交易策略
-----------------------

查看所有的内置交易策略，或者根据ID筛选部分交易策略。使用下面的函数：

下面的函数接受相同的参数stg_id，但是返回不同类型的数据，如果stg_id为None，则返回所有的内置交易策略，否则返回指定ID的交易策略。
如果用户输入的stg_id不存在，qteasy会根据用户输入的stg_id返回id与其最接近的交易策略。

下面的函数返回一个字典，字典的key是交易策略的ID，value是交易策略的说明文档。

.. autofunction:: qteasy.built_ins

下面的函数返回一个列表，列表的元素是交易策略的ID或者交易策略的名称。

.. autofunction:: qteasy.built_in_list

.. autofunction:: qteasy.built_in_strategies

如果要获取一个内置交易策略对象，需要使用下面的函数，根据用户输入的ID返回内置策略对象，
如果用户输入ID有误，函数会报错并给用户提供一个建议的ID：

.. autofunction:: qteasy.get_built_in_strategy

如果要查看内置交易策略的说明文档，需要使用下面的函数，根据用户输入的ID返回内置策略对象，
如果用户输入ID有误，函数会报错并给用户提供一个建议的ID：

.. autofunction:: qteasy.built_in_doc

所有内置交易策略
===================

下面是所有的内置交易策略的说明文档，用户可以根据自己的需求选择合适的交易策略。

不依赖其他技术分析包的交易策略
----------------------------------------

以下是一些不依赖其他技术分析包的交易策略，这些交易策略都是基于历史数据的简单计算，不需要其他技术分析包的支持，可以直接调用。

简单选股策略
------------

根据历史数据选股

.. autofunction:: qteasy.built_in.SelectingAvgIndicator

.. autofunction:: qteasy.built_in.SelectingNDayLast

.. autofunction:: qteasy.built_in.SelectingNDayAvg

.. autofunction:: qteasy.built_in.SelectingNDayChange

.. autofunction:: qteasy.built_in.SelectingNDayRateChange

.. autofunction:: qteasy.built_in.SelectingNDayVolatility

.. autofunction:: qteasy.built_in.SignalNone

.. autofunction:: qteasy.built_in.SellRate

.. autofunction:: qteasy.built_in.BuyRate

.. autofunction:: qteasy.built_in.SelectingAll

.. autofunction:: qteasy.built_in.SelectingNone

.. autofunction:: qteasy.built_in.SelectingRandom

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

.. autofunction:: qteasy.built_in.CROSSLINE

.. autofunction:: qteasy.built_in.CDL

.. autofunction:: qteasy.built_in.SoftBBand

.. autofunction:: qteasy.built_in.BBand


依赖``TA-Lib``技术分析包的交易策略
----------------------------------------

以下是一些依赖``TA-Lib``技术分析包的交易策略，这些交易策略都是基于``TA-Lib``技术分析包的计算，需要安装``TA-Lib``技术分析包。


基于单均线穿越的择时策略
------------------------

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

