# QTEASY使用教程04——使用内置交易策略

qteasy提供了多种内置交易策略，用户可以很容易地直接使用这些交易策略，同时，qteasy提供了一套交易策略组合机制，用户可以将多个简单的交易策略组合成一个比较复杂的交易策略，策略的组合方式是可以灵活设定的。将多个简单交易策略组合成一个复杂的策略后，同样可以使用策略优化工具搜索整个复杂策略的最佳参数。

在这篇教程中，您将了解如何使用内置交易策略，如何组合策略，如何设定组合规则实现复杂策略，以及如何优化策略。



```python
import qteasy as qt
```

    /Users/jackie/Library/CloudStorage/OneDrive-Personal/Projects/PycharmProjects/qteasy/qteasy/_arg_validators.py:829: UserWarning: config_key <tushare_token> is not a built-in parameter key, please check your input!
      warnings.warn(err_msg)


`qteasy`的内置交易策略可以通过qteasy.built_in模块来访问，通过以下几个方法可以获取内置策略的清单：

### `qt.built_ins()`

### `qt.built_in_strategies()`

### `qt.built_in_list()`

上面三个方法的输出是一样的，都用一个dict列出所有的内置交易策略，dict的key是交易策略的ID，value是交易策略对象。

### `qt.get_built_in_strategy(id)`

在qteasy中，可以直接使用策略的ID获取内置交易策略

除了使用qt.get_built_in_strategy()获取交易策略以外，在创建Operator对象的时候，将内置交易策略的ID作为参数传入，也可以直接创建交易策略。


```python
# 获取内置交易策略的ID
strategy_ids = qt.built_ins().keys()
print(list(strategy_ids)[:10])
```

    ['crossline', 'macd', 'dma', 'trix', 'cdl', 'bband', 's-bband', 'sarext', 'ssma', 'sdema']



```python
# 使用策略ID获取交易策略
stg = qt.get_built_in_strategy('trix')
# 显示策略的相关信息
stg.info()
```

    Strategy_type:      RuleIterator
    Strategy name:      TRIX
    Description:        TRIX strategy, determine long/short position according to triple exponential weighted moving average prices
    Strategy Parameter: (25, 125)
    
    Strategy Properties     Property Value
    ---------------------------------------
    Parameter count         2
    Parameter types         ['int', 'int']
    Parameter range         [(2, 50), (3, 150)]
    Data frequency          d
    Sample frequency        d
    Window length           270
    Data types              ['close']
    



```python
# 通过策略ID直接生成Operator
op = qt.Operator(strategies='dma, macd')
# 通过op.get_stg或op[]获取交易策略
stg_dma = op.get_stg('dma')
stg_macd = op['macd']

# 查看两个交易策略的相关信息
stg_dma.info()
stg_macd.info()
```

    Strategy_type:      RuleIterator
    Strategy name:      DMA
    Description:        Quick DMA strategy, determine long/short position according to differences of moving average prices with simple timing strategy
    Strategy Parameter: (12, 26, 9)
    
    Strategy Properties     Property Value
    ---------------------------------------
    Parameter count         3
    Parameter types         ['int', 'int', 'int']
    Parameter range         [(10, 250), (10, 250), (10, 250)]
    Data frequency          d
    Sample frequency        d
    Window length           270
    Data types              ['close']
    
    Strategy_type:      RuleIterator
    Strategy name:      MACD
    Description:        MACD strategy, determine long/short position according to differences of exponential weighted moving average prices
    Strategy Parameter: (12, 26, 9)
    
    Strategy Properties     Property Value
    ---------------------------------------
    Parameter count         3
    Parameter types         ['int', 'int', 'int']
    Parameter range         [(10, 250), (10, 250), (10, 250)]
    Data frequency          d
    Sample frequency        d
    Window length           270
    Data types              ['close']
    


目前qteasy支持的内置交易策略如下：

| ID    | 策略名称    |   说明   | 
|:------- |:--------:|:--------- |
| crossline | `TimingCrossline` | crossline择时策略类，利用长短均线的交叉确定多空状态<br />1，当短均线位于长均线上方，且距离大于l*m%时，设置仓位目标为1<br />2，当短均线位于长均线下方，且距离大于l*mM时，设置仓位目标为-1<br />3，当长短均线之间的距离不大于l*m%时，设置仓位目标为0|
| macd | `TimingMACD` | MACD择时策略类，运用MACD均线策略，生成目标仓位百分比:<br />1，当MACD值大于0时，设置仓位目标为1<br />2，当MACD值小于0时，设置仓位目标为0|
| dma | `TimingDMA` | DMA择时策略<br />1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线后，输出为1<br />2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线后，输出为0|
| trix | `TimingTRIX` | TRIX择时策略，使用股票价格的三重平滑指数移动平均价格进行多空判断:<br />计算价格的三重平滑指数移动平均价TRIX，再计算M日TRIX的移动平均：<br />1， TRIX位于MATRIX上方时，设置仓位目标为1<br />2， TRIX位于MATRIX下方时，设置仓位目标位-1|
| cdl | `TimingCDL` | CDL择时策略，在K线图中找到符合要求的cdldoji模式<br />搜索历史数据窗口内出现的cdldoji模式（匹配度0～100之间），加总后/100，计算 等效cdldoji匹配数量，以匹配数量为交易信号。|
| bband | TimingBBand | 布林带线交易策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空，在价格上穿或下穿布林带线上下轨时产生交易信号。布林带线的均线类型不可选<br />1，当价格上穿上轨时，产生全仓买入信号<br />2，当价格下穿下轨时，产生全仓卖出信号|
| s-bband | SoftBBand | 布林带线渐进交易策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空，交易信号不是一次性产生的，而是逐步渐进买入和卖出。计算BBAND，检查价格是否超过BBAND的上轨或下轨：<br />1，当价格大于上轨后，每天产生10%的比例买入交易信号<br />2，当价格低于下轨后，每天产生33%的比例卖出交易信号|
| sarext | `TimingSAREXT` | 扩展抛物线SAR策略，当指标大于0时发出买入信号，当指标小于0时发出卖出信号|
| ssma | `SCRSSMA` | 单均线交叉策略——SMA均线(简单移动平均线)：根据股价与SMA均线的相对位置设定持仓比例|
| sdema | `SCRSDEMA` | 单均线交叉策略——DEMA均线(双重指数平滑移动平均线)：根据股价与DEMA均线的相对位置设定持仓比例|
| sema | `SCRSEMA` | 单均线交叉策略——EMA均线(指数平滑移动均线)：根据股价与EMA均线的相对位置设定持仓比例|
| sht | `SCRSHT` | 单均线交叉策略——HT(希尔伯特变换瞬时趋势线)：根据股价与HT线的相对位置设定持仓比例|
| skama | `SCRSKAMA` | 单均线交叉策略——KAMA均线(考夫曼自适应移动均线)：根据股价与KAMA均线的相对位置设定持仓比例|
| smama | `SCRSMAMA` | 单均线交叉策略——MAMA均线(MESA自适应移动平均线)：根据股价与MAMA均线的相对位置设定持仓比例|
| st3 | `SCRST3` | 单均线交叉策略——T3均线(三重指数平滑移动平均线)：根据股价与T3均线的相对位置设定持仓比例|
| stema | `SCRSTEMA` | 单均线交叉策略——TEMA均线(三重指数平滑移动平均线)：根据股价与TEMA均线的相对位置设定持仓比例|
| strima | `SCRSTRIMA` | 单均线交叉策略——TRIMA均线(三重指数平滑移动平均线)：根据股价与TRIMA均线的相对位置设定持仓比例|
| swma | `SCRSWMA` | 单均线交叉策略——WMA均线(加权移动平均线)：根据股价与WMA均线的相对位置设定持仓比例|
| dsma | `DCRSSMA` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于SMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| ddema | `DCRSDEMA` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于DEMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| dema | `DCRSEMA` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于EMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| dkama | `DCRSKAMA` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于KAMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| dmama | `DCRSMAMA` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于MAMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| dt3 | `DCRST3` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于T3均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| dtema | `DCRSTEMA` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于TEMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| dtrima | `DCRSTRIMA` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于TRIMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| dwma | `DCRSWMA` | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于WMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例|
| slsma | `SLPSMA` | 均线斜率交易策略——SMA均线(简单移动平均线)：<br />基于SMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| sldema | `SLPDEMA` | 均线斜率交易策略——DEMA均线(双重指数平滑移动平均线)：<br />基于DEMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| slema | `SLPEMA` | 均线斜率交易策略——EMA均线(指数平滑移动平均线)：<br />基于EMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| slht | `SLPHT` | 均线斜率交易策略——HT均线(希尔伯特变换——瞬时趋势线线)：<br />基于HT计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| slkama | `SLPKAMA` | 均线斜率交易策略——KAMA均线(考夫曼自适应移动平均线)：<br />基于KAMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| slmama | `SLPMAMA` | 均线斜率交易策略——MAMA均线(MESA自适应移动平均线)：<br />基于MAMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| slt3 | `SLPT3` | 均线斜率交易策略——T3均线(三重指数平滑移动平均线)：<br />基于T3计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| sltema | `SLPTEMA` | 均线斜率交易策略——TEMA均线(三重指数平滑移动平均线)：<br />基于TEMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| sltrima | `SLPTRIMA` | 均线斜率交易策略——TRIMA均线(三重指数平滑移动平均线)：<br />基于TRIMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| slwma | `SLPWMA` | 均线斜率交易策略——WMA均线(加权移动平均线)：<br />基于WMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标|
| adx | `ADX` | ADX指标（平均定向运动指数）选股策略：<br />基于ADX指标判断当前趋势的强度，从而根据趋势强度产生交易信号<br />1, 当ADX大于25时，判断趋势向上，设定持仓比例为1<br />2, 当ADX介于20到25之间时，判断为中性趋势，设定持仓比例为0<br />3, 当ADX小于20时，判断趋势向下，设定持仓比例为-1|
| apo | `APO` | APO指标（绝对价格震荡指标）选股策略：<br />基于APO指标判断当前股价变动的牛熊趋势，从而根据趋势产生交易信号<br />1, 当APO大于0时，判断为牛市趋势，设定持仓比例为1<br />2, 当ADX小于0时，判断为熊市趋势，设定持仓比例为-1|
| aroon | `AROON` | AROON指标选股策略：<br />通过计算AROON指标趋势的强弱程度输出强多/空头和弱多/空头<br />1, 当UP在DOWN的上方时，输出弱多头<br />2, 当UP位于DOWN下方时，输出弱空头<br />3, 当UP大于70且DOWN小于30时，输出强多头<br />4, 当UP小于30且DOWN大于70时，输出强空头|
| aroonosc | `AROONOSC` | AROON Oscillator (AROON震荡指标) 选股策略：<br />当AROONOSC大于0时表示价格趋势向上，反之趋势向下，绝对值大于50时表示强烈的趋势<br />1, 当AROONOSC大于0时，输出弱多头<br />2, 当AROONOSC小于0时，输出弱空头<br />3, 当AROONOSC大于50时，输出强多头<br /> 4, 当AROONOSC小于-50时，输出强空头|
| cci | `CCI` | CCI (Commodity Channel Index商品渠道指数) 选股策略：<br />CCI商品渠道指数被用来判断当前股价位于超卖还是超买区间，本策略使用这个指标生成投资仓位目标<br />1, 当CCI大于0时，输出弱多头<br />2, 当CCI小于0时，输出弱空头<br />3, 当CCI大于50时，输出强多头<br />4, 当CCI小于-50时，输出强空头|
| cmo | `CMO` | CMO (Chande Momentum Oscillator 钱德动量振荡器) 选股策略：<br />CMO 是一个在-100到100之间波动的动量指标，它被用来判断当前股价位于超卖还是超买区间，本策略使用这个指标生成投资仓位目标<br />1, 当CMO大于0时，输出弱多头<br />2, 当CMO小于0时，输出弱空头<br />3, 当CMO大于50时，输出强多头<br />4, 当CMO小于-50时，输出强空头|
| macdext | `MACDEXT` | MACDEXT (Extendec MACD 扩展MACD指数) 选股策略：<br />本策略使用MACD指标生成持仓目标，但是与标准的MACD不同，MACDEXT的快、慢、及信号均线的类型均可选<br />1, 当hist>0时输出多头<br />2, 当hist<0时输出空头|
| mfi | `MFI` | MFI (Money Flow Index 货币流向指数) 交易策略：<br />MFI指数用于判断股价属于超买还是超卖状态，本策略使用MFI指标生成交易信号<br />1, 当MFI>20时，持续不断产生10%买入交易信号<br />2, 当MFI>80时，持续不断产生30%卖出交易信号，持续卖出持仓股票|
| di | `DI` | DI (Directory Indicator 方向指标) 交易策略：<br />DI 指标包含负方向指标与正方向指标，它们分别表示价格上行和下行的趋势强度，本策略使用±DI指标生成交易信号<br />1, 当+DI > -DI时，设置持仓目标为1<br /> 2, 当+DI < -DI时，设置持仓目标为-1|
| dm | `DM` | DM (Directional Movement 方向运动指标) 交易策略：<br />DM 指标包含负方向运动指标(Negative Directional Movement)与正方向运动指标(Positive Directional Movement)，它们分别表示价格上行和下行的趋势，本策略使用±DM指标生成交易信号<br />1, 当+DM > -DM时，设置持仓目标为1<br />2, 当+DM < -DM时，设置持仓目标为-1<br />3, 其余情况设置持仓目标为0|
| mom | `MOM` | MOM (momentum indicator 动量指标) 交易策略：<br />MOM 指标可以用于识别价格的上行或下行趋势的强度，当前价格高于N日前价格时，MOM为正，反之为负。<br />1, 当MOM > 0时，设置持仓目标为1<br />2, 当MOM < 0时，设置持仓目标为-1<br />3, 其余情况设置持仓目标为0|
| ppo | `PPO` | PO (Percentage Price Oscillator 百分比价格振荡器) 交易策略：<br />PPO 指标表示快慢两根移动均线之间的百分比差值，用于判断价格的变化趋势。长短均线的计算周期和均线类型均为策略参数。<br />1, 当PPO > 0时，设置持仓目标为1<br />2, 当PPO < 0时，设置持仓目标为-1<br />3, 其余情况设置持仓目标为0|
| rsi | `RSI` | RSI (Relative Strength Index 相对强度指数) 交易策略：<br />RSI 指标度量最近价格变化的幅度，从而判断目前股票属于超卖还是超买状态<br />1, 当RSI > ulim时，设置持仓目标为1<br />2, 当RSI < llim时，设置持仓目标为-1<br />3, 其余情况设置持仓目标为0|
| stoch | `STOCH` | STOCH (Stochastic Indicator 随机指数) 交易策略：<br />STOCH 指标度量价格变化的动量，并且动量的大小判断价格趋势，并生成比例买卖交易信号。<br />1, 当k > 80时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当k < 20时，产生逐步买入信号，每周期买入总投资额的10%|
| stochf | `STOCHF` | STOCHF (Stochastic Fast Indicator 快速随机指标) 交易策略：<br /> STOCHF 指标度量价格变化的动量，与STOCH策略类似，使用快速随机指标判断价格趋势，并生成比例买卖交易信号。<br />1, 当k > 80时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当k < 20时，产生逐步买入信号，每周期买入总投资额的10%|
| stochrsi | `STOCHRSI` | STOCHRSI (Stochastic Relative Strength Index 随机相对强弱指标) 交易策略：<br />STOCHRSI 指标度量价格变化的动量，该指标在0～1之间波动，表示相对的价格趋势强弱程度，并生成比例买卖交易信号<br />1, 当k > 0.8时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当k < 0.2时，产生逐步买入信号，每周期买入总投资额的10%|
| ultosc | `ULTOSC` | ULTOSC (Ultimate Oscillator Indicator 终极振荡器指标) 交易策略：<br />ULTOSC 指标通过三个不同的时间跨度计算价格动量，并根据多种不同动量之间的偏离值生成交易信号。<br />1, 当ULTOSC > u时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当ULTOSC < l时，产生逐步买入信号，每周期买入总投资额的10%|
| willr | `WILLR` | WILLR (William's %R 威廉姆斯百分比) 交易策略：<br />WILLR 指标被用于计算股价当前处于超买还是超卖区间，并用于生成交易信号<br />1, 当WILLR > -l时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当WILLR < -u时，产生逐步买入信号，每周期买入总投资额的10%|
| signal_none | `SignalNone` | 空交易信号策略：不生成任何交易信号的策略|
| sellrate | `SellRate` | 变化率卖出信号策略：当价格的变化率超过阈值时，产生卖出信号<br />1，当change > 0，且day日涨幅大于change时，产生-1卖出信号<br />2，当change < 0，且day日跌幅大于change时，产生-1卖出信号|
| buyrate | `BuyRate` | 变化率买入信号策略：当价格的变化率超过阈值时，产生买入信号<br />1，当change > 0，且day日涨幅大于change时，产生1买入信号<br />2，当change < 0，且day日跌幅大于change时，产生1买入信号|
| long | `TimingLong` | 简单择时策略，整个历史周期上固定保持多头全仓状态|
| short | `TimingShort` | 简单择时策略，整个历史周期上固定保持空头全仓状态|
| zero | `TimingZero` | 简单择时策略，整个历史周期上固定保持空仓状态|
| all | `SelectingAll` | 保持历史股票池中的所有股票都被选中，投资比例平均分配|
| select_none | `SelectingNone` | 保持历史股票池中的所有股票都不被选中，投资仓位为0|
| random | `SelectingRandom` | 在每个历史分段中，按照指定的比例（p<1时）随机抽取若干股票，或随机抽取指定数量（p>=1）的股票进入投资组合，投资比例平均分配|
| finance | `SelectingAvgIndicator` | 以股票过去一段时间内的财务指标的平均值作为选股因子选股，基础选股策略：以股票的历史指标的平均值作为选股因子，因子排序参数可以作为策略参数传入，改变策略数据类型，根据不同的历史数据选股，选股参数可以通过pars传入|
| ndaylast | `SelectingNDayLast` | 以股票N天前的价格或数据指标作为选股因子选股|
| ndayavg | `SelectingNDayAvg` | 以股票过去N天的价格或数据指标的平均值作为选股因子选股|
| ndayrate | `SelectingNDayRateChange` | 以股票过去N天的价格或数据指标的变动比例作为选股因子选股|
| ndaychg | `SelectingNDayChange` | 以股票过去N天的价格或数据指标的变动值作为选股因子选股|
| ndayvol | `SelectingNDayVolatility` | 根据股票以前N天的股价波动率作为选股因子


```python

```

如果需要查看每一个内置交易策略的详细解释，例如策略参数的含义、信号生成规则，可以查看每一个交易策略的Doc-string：

例如：

```python
qt.built_in.TimingCrossline?
```
可以看到
```
Init signature: qt.built_in.TimingCrossline(pars:tuple=(35, 120, 0.02))
Docstring:     
crossline择时策略类，利用长短均线的交叉确定多空状态

策略参数：
    s: int, 短均线计算日期；
    l: int, 长均线计算日期；
    m: float, 均线边界宽度（百分比）；
信号类型：
    PT型：目标仓位百分比
信号规则：
    1，当短均线位于长均线上方，且距离大于l*m%时，设置仓位目标为1
    2，当短均线位于长均线下方，且距离大于l*mM时，设置仓位目标为-1
    3，当长短均线之间的距离不大于l*m%时，设置仓位目标为0

策略属性缺省值：
默认参数：(35, 120, 0.02)
数据类型：close 收盘价，单数据输入
采样频率：天
窗口长度：270
参数范围：[(10, 250), (10, 250), (0, 1)]
策略不支持参考数据，不支持交易数据
File:           ~/Library/CloudStorage/OneDrive-Personal/Projects/PycharmProjects/qteasy/qteasy/built_in.py
Type:           type
Subclasses:     
```

又例如：

```python
qt.built_in.SelectingNDayRateChange?
```

可以看到：

```
Init signature: qt.built_in.SelectingNDayRateChange(pars=(14,))
Docstring:     
基础选股策略：根据股票以前n天的股价变动比例作为选股因子

策略参数：
    n: int, 股票历史数据的选择期
信号类型：
    PT型：百分比持仓比例信号
信号规则：
    在每个选股周期使用以前n天的股价变动比例作为选股因子进行选股
    通过以下策略属性控制选股方法：
    *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
    *condition:         str ,   确定股票的筛选条件，默认值'any'
                                'any'        :默认值，选择所有可用股票
                                'greater'    :筛选出因子大于ubound的股票
                                'less'       :筛选出因子小于lbound的股票
                                'between'    :筛选出因子介于lbound与ubound之间的股票
                                'not_between':筛选出因子不在lbound与ubound之间的股票
    *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
    *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
    *sort_ascending:    bool,   排序方法，默认值: False,
                                True: 优先选择因子最小的股票,
                                False, 优先选择因子最大的股票
    *weighting:         str ,   确定如何分配选中股票的权重
                                默认值: 'even'
                                'even'       :所有被选中的股票都获得同样的权重
                                'linear'     :权重根据因子排序线性分配
                                'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                'proportion' :权重与股票的因子分值成正比

策略属性缺省值：
默认参数：(14,)
数据类型：close 收盘价，单数据输入
采样频率：月
窗口长度：150
参数范围：[(2, 150)]
策略不支持参考数据，不支持交易数据
File:           ~/Library/CloudStorage/OneDrive-Personal/Projects/PycharmProjects/qteasy/qteasy/built_in.py
Type:           type
Subclasses:    
```

## 多重策略以及策略组合

在qteasy中，一个Operator交易员对象可以同时运行多个交易策略。这些交易策略在运行的时候，都会分别提取各自所需的历史数据，独立生成不同的交易信号，这些交易信号会被组合成一组交易信号，统一执行。

利用这种特性，用户可以在一个交易员对象中同时运行多个各有侧重的交易策略，例如，一个交易策略监控个股的股价，根据股价产生择信号，第二个交易策略专门负责监控大盘走势，通过大盘走势决定整体仓位。第三个交易策略专门负责止盈止损，在特定时刻止损。最终的交易信号以第一个交易策略为主，但受到第二个策略的节制，必要时会被第三个策略完全控制。

或者，用户也可以很容易地制定出一个“委员会”策略，在一个综合性策略中由多个策略独立地做出交易决策，最终的交易信号由所有子策略组成的”委员会“投票决定，投票的方式可以是简单多数、绝对多数、加权投票结果等等。

上述交易策略组合中，每一个独立的交易策略都很简单，很容易定义，而将他们组合起来，又能发挥更大的作用。同时每一个子策略都是独立的，可以自由组合出复杂的综合性交易策略。这样可以避免不断地重复开发策略，只需要对子策略重新排列组合，重新定义组合方式，就可以快速地搭建一系列的复杂综合性交易策略。相信这样能够极大地提高交易策略的搭建效率，缩短周期。时间就是金钱。

### 定义策略组合方式blender

qteasy中的组合策略是由blender实现的。在一个Operator中，如果策略的数量多于1个，就必须定义一个blender。如果没有明确定义blender，而策略的数量超过1个时，qteasy会在运行Operator的时候创建一个默认的blender，但是为了让多重策略正确运行，用户需要自行定义blender。

blender是用户自行定义的一个组合表达式，用户使用这个表达式确定不同交易策略的组合方式。这个组合表达式可以包含四则运算符以及常见数学函数，例如：

当一个Operator对象中有三个交易策略时，可以按照以下方式定义blender：

#### 使用四则运算符定义blender表达式

$$ 1 + 2 + 3 $$ 

此时三个交易策略生成的交易信号会被加起来，成为最终的交易信号，如果策略1的结果为买入10%，策略2结果为买入10%，策略3结果为买入30%，则最终的结果为买入50%

#### 使用逻辑运算符定义blender表达式：

$$ 1\ and\ 2\ and\ 3 $$

表示只有当交易策略1、2、3都出现交易信号的时候，才会最终形成交易信号。如策略1的结果为买入，策略2结果为买入，而策略3没有交易信号，则最终的结果为没有交易信号。

#### blender表达式中还可以包含括号和一些函数：

$$ max(1, 2) + 3 $$

表示策略1、2的结果中最大值与策略3的结果相加，成为最终交易信号。如果策略1的结果为买入10%，策略2结果为买入20%，策略3结果为买入30%，最终的结果为买入50%

blender表达式中支持的一些特殊函数如下：


| 函数 | 表达式 | 说明 |
|:--:|:--:|:--|
| op_avg | `op_avg()` | 平均值函数 |
| op_pos | `op_pos()` | 累计值函数 |
| op_avg_pos | `op_avg_pos()` | 平均值累计函数 |
| op_str | `op_str()` | 强度累计函数 |
| op_sum | `op_sum()`  | 组合值函数 |


以下方法可以被用来设置或获取策略的blender

### `operator.set_blender(price_type=None, blender=None)`
设置blender


### `operator.view_blender()`
查看blender



```python

```

### 备用信息，qteasy内置策略表完整信息：

|ID| 策略名 | type | signal | description | par | data |
|:--:|:--:|:--:|:--:|:--|:--:|:--:|
| crossline | TimingCrossline | 均线择时 | PT | crossline择时策略类，利用长短均线的交叉确定多空状态<br />1，当短均线位于长均线上方，且距离大于l*m%时，设置仓位目标为1<br />2，当短均线位于长均线下方，且距离大于l*mM时，设置仓位目标为-1<br />3，当长短均线之间的距离不大于l*m%时，设置仓位目标为0 | (35, 120, 0.02) | close |
| macd | TimingMACD | 动量择时 | PS | MACD择时策略类，运用MACD均线策略，生成目标仓位百分比:<br />1，当MACD值大于0时，设置仓位目标为1<br />2，当MACD值小于0时，设置仓位目标为0 | (12, 26, 9) | close |
| dma | TimingDMA | 动量择时 | VS | DMA择时策略<br />1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线后，输出为1<br />2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线后，输出为0 | (12, 26, 9) | close |
| trix | TimingTRIX | 动量择时 | PS | TRIX择时策略，使用股票价格的三重平滑指数移动平均价格进行多空判断:<br />计算价格的三重平滑指数移动平均价TRIX，再计算M日TRIX的移动平均：<br />1， TRIX位于MATRIX上方时，设置仓位目标为1<br />2， TRIX位于MATRIX下方时，设置仓位目标位-1 | (25, 125) | close |
| cdl | TimingCDL | K线形态择时 | PS | CDL择时策略，在K线图中找到符合要求的cdldoji模式<br />搜索历史数据窗口内出现的cdldoji模式（匹配度0～100之间），加总后/100，计算 等效cdldoji匹配数量，以匹配数量为交易信号。 | () | open, high, low, close |
| bband | TimingBBand | 均线择时 | PT | 布林带线交易策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空，在价格上穿或下穿布林带线上下轨时产生交易信号。布林带线的均线类型不可选<br />1，当价格上穿上轨时，产生全仓买入信号<br />2，当价格下穿下轨时，产生全仓卖出信号 | (20, 2, 2) | close |
| s-bband | SoftBBand | 均线择时 | PT | 布林带线渐进交易策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空，交易信号不是一次性产生的，而是逐步渐进买入和卖出。计算BBAND，检查价格是否超过BBAND的上轨或下轨：<br />1，当价格大于上轨后，每天产生10%的比例买入交易信号<br />2，当价格低于下轨后，每天产生33%的比例卖出交易信号 | (20, 2, 2, 0) | close |
| sarext | TimingSAREXT | 动量择时 | PT | 扩展抛物线SAR策略，当指标大于0时发出买入信号，当指标小于0时发出卖出信号 | (0, 3) | high, low |
| ssma | SCRSSMA | 单均线择时 | PT | 单均线交叉策略——SMA均线(简单移动平均线)：根据股价与SMA均线的相对位置设定持仓比例 | (14,) | close |
| sdema | SCRSDEMA | 单均线择时 | PT | 单均线交叉策略——DEMA均线(双重指数平滑移动平均线)：根据股价与DEMA均线的相对位置设定持仓比例 | (14,) | close |
| sema | SCRSEMA | 单均线择时 | PT | 单均线交叉策略——EMA均线(指数平滑移动均线)：根据股价与EMA均线的相对位置设定持仓比例 | (14,) | close |
| sht | SCRSHT | 单均线择时 | PT | 单均线交叉策略——HT(希尔伯特变换瞬时趋势线)：根据股价与HT线的相对位置设定持仓比例 | () | close |
| skama | SCRSKAMA | 单均线择时 | PT | 单均线交叉策略——KAMA均线(考夫曼自适应移动均线)：根据股价与KAMA均线的相对位置设定持仓比例 | (14,) | close |
| smama | SCRSMAMA | 单均线择时 | PT | 单均线交叉策略——MAMA均线(MESA自适应移动平均线)：根据股价与MAMA均线的相对位置设定持仓比例 | (0.5, 0.05) | close |
| st3 | SCRST3 | 单均线择时 | PT | 单均线交叉策略——T3均线(三重指数平滑移动平均线)：根据股价与T3均线的相对位置设定持仓比例 | (12, 0.5) | close |
| stema | SCRSTEMA | 单均线择时 | PT | 单均线交叉策略——TEMA均线(三重指数平滑移动平均线)：根据股价与TEMA均线的相对位置设定持仓比例 | (6,) | close |
| strima | SCRSTRIMA | 单均线择时 | PT | 单均线交叉策略——TRIMA均线(三重指数平滑移动平均线)：根据股价与TRIMA均线的相对位置设定持仓比例 | (14,) | close |
| swma | SCRSWMA | 单均线择时 | PT | 单均线交叉策略——WMA均线(加权移动平均线)：根据股价与WMA均线的相对位置设定持仓比例 | (14,) | close |
| dsma | DCRSSMA | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于SMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (125, 25) | close |
| ddema | DCRSDEMA | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于DEMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (125, 25) | close |
| dema | DCRSEMA | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于EMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (125, 25) | close |
| dkama | DCRSKAMA | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于KAMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (125, 25) | close |
| dmama | DCRSMAMA | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于MAMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (0.15, 0.05, 0.55, 0.25) | close |
| dt3 | DCRST3 | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于T3均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (20, 0.5, 5, 0.5) | close |
| dtema | DCRSTEMA | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于TEMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (11, 6) | close |
| dtrima | DCRSTRIMA | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于TRIMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (125, 25) | close |
| dwma | DCRSWMA | 双均线择时 | PT | 双均线交叉策略——SMA均线(简单移动平均线)：<br />基于WMA均线计算规则生成快慢两根均线，根据快与慢两根均线的相对位置设定持仓比例 | (125, 25) | close |
| slsma | SLPSMA | 均线斜率则时 | PT | 均线斜率交易策略——SMA均线(简单移动平均线)：<br />基于SMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (35, 5) | close |
| sldema | SLPDEMA | 均线斜率则时 | PT | 均线斜率交易策略——DEMA均线(双重指数平滑移动平均线)：<br />基于DEMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (35, 5) | close |
| slema | SLPEMA | 均线斜率则时 | PT | 均线斜率交易策略——EMA均线(指数平滑移动平均线)：<br />基于EMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (35, 5) | close |
| slht | SLPHT | 均线斜率则时 | PT | 均线斜率交易策略——HT均线(希尔伯特变换——瞬时趋势线线)：<br />基于HT计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (5,) | close |
| slkama | SLPKAMA | 均线斜率则时 | PT | 均线斜率交易策略——KAMA均线(考夫曼自适应移动平均线)：<br />基于KAMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (35, 5) | close |
| slmama | SLPMAMA | 均线斜率则时 | PT | 均线斜率交易策略——MAMA均线(MESA自适应移动平均线)：<br />基于MAMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (0.5, 0.05, 5) | close |
| slt3 | SLPT3 | 均线斜率则时 | PT | 均线斜率交易策略——T3均线(三重指数平滑移动平均线)：<br />基于T3计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (12, 0.25, 5) | close |
| sltema | SLPTEMA | 均线斜率则时 | PT | 均线斜率交易策略——TEMA均线(三重指数平滑移动平均线)：<br />基于TEMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (6, 5) | close |
| sltrima | SLPTRIMA | 均线斜率则时 | PT | 均线斜率交易策略——TRIMA均线(三重指数平滑移动平均线)：<br />基于TRIMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (35, 5) | close |
| slwma | SLPWMA | 均线斜率则时 | PT | 均线斜率交易策略——WMA均线(加权移动平均线)：<br />基于WMA计算规则生成移动均线，根据均线的斜率设定持仓比例目标 | (125, 5) | close |
| adx | ADX | 动量择时 | PT | ADX指标（平均定向运动指数）选股策略：<br />基于ADX指标判断当前趋势的强度，从而根据趋势强度产生交易信号<br />1, 当ADX大于25时，判断趋势向上，设定持仓比例为1<br />2, 当ADX介于20到25之间时，判断为中性趋势，设定持仓比例为0<br />3, 当ADX小于20时，判断趋势向下，设定持仓比例为-1 | (14,) | high, low, close |
| apo | APO | 动量择时 | PT | APO指标（绝对价格震荡指标）选股策略：<br />基于APO指标判断当前股价变动的牛熊趋势，从而根据趋势产生交易信号<br />1, 当APO大于0时，判断为牛市趋势，设定持仓比例为1<br />2, 当ADX小于0时，判断为熊市趋势，设定持仓比例为-1 | (12, 26, 0) | close |
| aroon | AROON | 动量择时 | PT | AROON指标选股策略：<br />通过计算AROON指标趋势的强弱程度输出强多/空头和弱多/空头<br />1, 当UP在DOWN的上方时，输出弱多头<br />2, 当UP位于DOWN下方时，输出弱空头<br />3, 当UP大于70且DOWN小于30时，输出强多头<br />4, 当UP小于30且DOWN大于70时，输出强空头 | (14,) | high, low |
| aroonosc | AROONOSC | 动量择时 | PT | AROON Oscillator (AROON震荡指标) 选股策略：<br />当AROONOSC大于0时表示价格趋势向上，反之趋势向下，绝对值大于50时表示强烈的趋势<br />1, 当AROONOSC大于0时，输出弱多头<br />2, 当AROONOSC小于0时，输出弱空头<br />3, 当AROONOSC大于50时，输出强多头<br /> 4, 当AROONOSC小于-50时，输出强空头 | (14,) | high, low |
| cci | CCI | 动量择时 | PT | CCI (Commodity Channel Index商品渠道指数) 选股策略：<br />CCI商品渠道指数被用来判断当前股价位于超卖还是超买区间，本策略使用这个指标生成投资仓位目标<br />1, 当CCI大于0时，输出弱多头<br />2, 当CCI小于0时，输出弱空头<br />3, 当CCI大于50时，输出强多头<br />4, 当CCI小于-50时，输出强空头 | (14,) | high, low, close |
| cmo | CMO | 动量择时 | PS | CMO (Chande Momentum Oscillator 钱德动量振荡器) 选股策略：<br />CMO 是一个在-100到100之间波动的动量指标，它被用来判断当前股价位于超卖还是超买区间，本策略使用这个指标生成投资仓位目标<br />1, 当CMO大于0时，输出弱多头<br />2, 当CMO小于0时，输出弱空头<br />3, 当CMO大于50时，输出强多头<br />4, 当CMO小于-50时，输出强空头 | (14,) | high, low, close |
| macdext | MACDEXT | 动量择时 | PT | MACDEXT (Extendec MACD 扩展MACD指数) 选股策略：<br />本策略使用MACD指标生成持仓目标，但是与标准的MACD不同，MACDEXT的快、慢、及信号均线的类型均可选<br />1, 当hist>0时输出多头<br />2, 当hist<0时输出空头 | (12, 0, 26, 0, 9, 0) | high, low, close |
| mfi | MFI | 动量择时 | PT | MFI (Money Flow Index 货币流向指数) 交易策略：<br />MFI指数用于判断股价属于超买还是超卖状态，本策略使用MFI指标生成交易信号<br />1, 当MFI>20时，持续不断产生10%买入交易信号<br />2, 当MFI>80时，持续不断产生30%卖出交易信号，持续卖出持仓股票 | (14,) | high, low, close, volume |
| di | DI | 动量择时 | PT | DI (Directory Indicator 方向指标) 交易策略：<br />DI 指标包含负方向指标与正方向指标，它们分别表示价格上行和下行的趋势强度，本策略使用±DI指标生成交易信号<br />1, 当+DI > -DI时，设置持仓目标为1<br /> 2, 当+DI < -DI时，设置持仓目标为-1 | (14, 14) | high, low, close |
| dm | DM | 动量择时 | PT | DM (Directional Movement 方向运动指标) 交易策略：<br />DM 指标包含负方向运动指标(Negative Directional Movement)与正方向运动指标(Positive Directional Movement)，它们分别表示价格上行和下行的趋势，本策略使用±DM指标生成交易信号<br />1, 当+DM > -DM时，设置持仓目标为1<br />2, 当+DM < -DM时，设置持仓目标为-1<br />3, 其余情况设置持仓目标为0 | (14, 14) | high, low |
| mom | MOM | 动量择时 | PT | MOM (momentum indicator 动量指标) 交易策略：<br />MOM 指标可以用于识别价格的上行或下行趋势的强度，当前价格高于N日前价格时，MOM为正，反之为负。<br />1, 当MOM > 0时，设置持仓目标为1<br />2, 当MOM < 0时，设置持仓目标为-1<br />3, 其余情况设置持仓目标为0 | (14, ) | close |
| ppo | PPO | 动量择时 | PS | PO (Percentage Price Oscillator 百分比价格振荡器) 交易策略：<br />PPO 指标表示快慢两根移动均线之间的百分比差值，用于判断价格的变化趋势。长短均线的计算周期和均线类型均为策略参数。<br />1, 当PPO > 0时，设置持仓目标为1<br />2, 当PPO < 0时，设置持仓目标为-1<br />3, 其余情况设置持仓目标为0 | (12, 26, 0) | close |
| rsi | RSI | 动量择时 | PS | RSI (Relative Strength Index 相对强度指数) 交易策略：<br />RSI 指标度量最近价格变化的幅度，从而判断目前股票属于超卖还是超买状态<br />1, 当RSI > ulim时，设置持仓目标为1<br />2, 当RSI < llim时，设置持仓目标为-1<br />3, 其余情况设置持仓目标为0 | (12, 70, 30) | close |
| stoch | STOCH | 动量择时 | PS | STOCH (Stochastic Indicator 随机指数) 交易策略：<br />STOCH 指标度量价格变化的动量，并且动量的大小判断价格趋势，并生成比例买卖交易信号。<br />1, 当k > 80时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当k < 20时，产生逐步买入信号，每周期买入总投资额的10% | (5, 3, 0, 3, 0) | high, low, close |
| stochf | STOCHF | 动量择时 | PS | STOCHF (Stochastic Fast Indicator 快速随机指标) 交易策略：<br /> STOCHF 指标度量价格变化的动量，与STOCH策略类似，使用快速随机指标判断价格趋势，并生成比例买卖交易信号。<br />1, 当k > 80时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当k < 20时，产生逐步买入信号，每周期买入总投资额的10% | (5, 3, 0) | high, low, close |
| stochrsi | STOCHRSI | 动量择时 | PS | STOCHRSI (Stochastic Relative Strength Index 随机相对强弱指标) 交易策略：<br />STOCHRSI 指标度量价格变化的动量，该指标在0～1之间波动，表示相对的价格趋势强弱程度，并生成比例买卖交易信号<br />1, 当k > 0.8时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当k < 0.2时，产生逐步买入信号，每周期买入总投资额的10% | (14, 5, 3, 0) | close |
| ultosc | ULTOSC | 动量择时 | PT | ULTOSC (Ultimate Oscillator Indicator 终极振荡器指标) 交易策略：<br />ULTOSC 指标通过三个不同的时间跨度计算价格动量，并根据多种不同动量之间的偏离值生成交易信号。<br />1, 当ULTOSC > u时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当ULTOSC < l时，产生逐步买入信号，每周期买入总投资额的10% | (7, 14, 28, 70, 30) | high, low, close |
| willr | WILLR | 动量择时 | PS | WILLR (William's %R 威廉姆斯百分比) 交易策略：<br />WILLR 指标被用于计算股价当前处于超买还是超卖区间，并用于生成交易信号<br />1, 当WILLR > -l时，产生逐步卖出信号，每周期卖出持有份额的30%<br />2, 当WILLR < -u时，产生逐步买入信号，每周期买入总投资额的10% | (14, 80, 20) | high, low, close |
| signal_none | SignalNone | 空策略 | PS | 空交易信号策略：不生成任何交易信号的策略 | () | close |
| sellrate | SellRate | 量价选股 | PT | 变化率卖出信号策略：当价格的变化率超过阈值时，产生卖出信号<br />1，当change > 0，且day日涨幅大于change时，产生-1卖出信号<br />2，当change < 0，且day日跌幅大于change时，产生-1卖出信号 | (20, 0.1) | close |
| buyrate | BuyRate | 量价选股 | PT | 变化率买入信号策略：当价格的变化率超过阈值时，产生买入信号<br />1，当change > 0，且day日涨幅大于change时，产生1买入信号<br />2，当change < 0，且day日跌幅大于change时，产生1买入信号 | (20, 0.1) | close |
| long | TimingLong | 简单择时 | PT | 简单择时策略，整个历史周期上固定保持多头全仓状态 | () | close |
| short | TimingShort | 简单择时 | PS | 简单择时策略，整个历史周期上固定保持空头全仓状态 | () | close |
| zero | TimingZero | 简单择时 | PT | 简单择时策略，整个历史周期上固定保持空仓状态 | () | close |
| all | SelectingAll | 简单选股 | PT | 保持历史股票池中的所有股票都被选中，投资比例平均分配 | () | close |
| select_none | SelectingNone | 简单选股 | PT | 保持历史股票池中的所有股票都不被选中，投资仓位为0 | () | close |
| random | SelectingRandom | 简单选股 | PT | 在每个历史分段中，按照指定的比例（p<1时）随机抽取若干股票，或随机抽取指定数量（p>=1）的股票进入投资组合，投资比例平均分配 | (0.5, ) | close |
| finance | SelectingAvgIndicator | 指标选股 | PT | 以股票过去一段时间内的财务指标的平均值作为选股因子选股，基础选股策略：以股票的历史指标的平均值作为选股因子，因子排序参数可以作为策略参数传入，改变策略数据类型，根据不同的历史数据选股，选股参数可以通过pars传入 | (True, 'even', 'greater', 0, 0, 0.25) | eps |
| ndaylast | SelectingNDayLast | 量价选股 | PT | 以股票N天前的价格或数据指标作为选股因子选股 | (2,) | close |
| ndayavg | SelectingNDayAvg | 量价选股 | PT | 以股票过去N天的价格或数据指标的平均值作为选股因子选股 | (14,) | close |
| ndayrate | SelectingNDayRateChange | 量价选股 | PT | 以股票过去N天的价格或数据指标的变动比例作为选股因子选股 | (14,) | close |
| ndaychg | SelectingNDayChange | 量价选股 | PT | 以股票过去N天的价格或数据指标的变动值作为选股因子选股 | (14,) | close |
| ndayvol | SelectingNDayVolatility | 量价选股 | PT | 根据股票以前N天的股价波动率作为选股因子 | (14,) | high,low,close


```python

```
