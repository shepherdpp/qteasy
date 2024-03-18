# 使用内置交易策略，组合成复杂策略

`qteasy`是一个完全本地化部署和运行的量化交易分析工具包，[Github地址在这里](https://github.com/shepherdpp/qteasy)，具备以下功能：

- 金融数据的获取、清洗、存储以及处理、可视化、使用
- 量化交易策略的创建，并提供大量内置基本交易策略
- 向量化的高速交易策略回测及交易结果评价
- 交易策略参数的优化以及评价
- 交易策略的部署、实盘运行

通过本系列教程，您将会通过一系列的实际示例，充分了解`qteasy`的主要功能以及使用方法。

## 开始前的准备工作

在开始本节教程前，请先确保您已经掌握了下面的内容：

- 安装、配置qteasy —— 详情请参阅[QTEASY教程1](1-get-started.md)
- 设置了一个本地数据源，并已经将足够的历史数据下载到本地（包括交易日历、股票/基金/指数基本信息、股票/基金/指数的价格数据以及财务指标或其他财务数据——详情请参阅[QTEASY教程2](2-get-data.md)
- 学会创建交易员对象，使用一个内置交易策略并回测其历史表现，检查回测日志、明白如何调整策略的运行参数或可调参数，改进策略的表现——[QTEASY教程3](3-start-first-strategy.md)

在[QTEASY文档](https://qteasy.readthedocs.io/zh/latest/)中，还能找到更多关于如何创建交易员对象运行策略，使用历史数据回测策略，检查回测交易记录，修改策略等等相关内容。对qteasy的基本使用方法还不熟悉的同学，可以移步那里查看更多详细说明。

## 本节的目标

在本节中，我们将了解如果使用qteasy`中更多的内置策略，如何使交易员同时运行多个交易策略，如何使用策略混合器(blender)来使用交易策略生成不同的组合策略，


目前qteasy支持超过70种内置交易策略，全部都是开箱即用，完整的内置交易策略清单请参见[参考文档](../references/4-build-in-strategy-blender.md)：

```python
# 获取内置交易策略的清单
stg_list = qt.built_ins('dma')
```
打印如下信息：

    DMA择时策略

    策略参数：
        s, int, 短均线周期
        l, int, 长均线周期
        d, int, DMA周期
    信号类型：
        PS型：百分比买卖交易信号
    信号规则：
        在下面情况下产生买入信号：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线后，输出为1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线后，输出为0
        3， DMA与股价发生背离时的交叉信号，可信度较高

    策略属性缺省值：
    默认参数：(12, 26, 9)
    数据类型：close 收盘价，单数据输入
    采样频率：天
    窗口长度：270
    参数范围：[(10, 250), (10, 250), (8, 250)]
    策略不支持参考数据，不支持交易数据


| ID        | 策略名称    | 说明                                                                                                                                                           | 
|:----------|:--------:|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| crossline | `TimingCrossline` | crossline择时策略类，利用长短均线的交叉确定多空状态<br />1，当短均线位于长均线上方，且距离大于l\*m%时，设置仓位目标为1<br />2，当短均线位于长均线下方，且距离大于l\*m%时，设置仓位目标为-1<br />3，当长短均线之间的距离不大于l\*m%时，设置仓位目标为0          |
| macd      | `TimingMACD` | MACD择时策略类，运用MACD均线策略，生成目标仓位百分比:<br />1，当MACD值大于0时，设置仓位目标为1<br />2，当MACD值小于0时，设置仓位目标为0                                                                        |
| dma       | `TimingDMA` | DMA择时策略<br />1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线后，输出为1<br />2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线后，输出为0                                                          |
| trix      | `TimingTRIX` | TRIX择时策略，使用股票价格的三重平滑指数移动平均价格进行多空判断:<br />计算价格的三重平滑指数移动平均价TRIX，再计算M日TRIX的移动平均：<br />1， TRIX位于MATRIX上方时，设置仓位目标为1<br />2， TRIX位于MATRIX下方时，设置仓位目标位-1             |
| cdl       | `TimingCDL` | CDL择时策略，在K线图中找到符合要求的cdldoji模式<br />搜索历史数据窗口内出现的cdldoji模式（匹配度0～100之间），加总后/100，计算 等效cdldoji匹配数量，以匹配数量为交易信号。                                                    |
| bband     | TimingBBand | 布林带线交易策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空，在价格上穿或下穿布林带线上下轨时产生交易信号。布林带线的均线类型不可选<br />1，当价格上穿上轨时，产生全仓买入信号<br />2，当价格下穿下轨时，产生全仓卖出信号                                     |
| s-bband   | SoftBBand | 布林带线渐进交易策略，根据股价与布林带上轨和布林带下轨之间的关系确定多空，交易信号不是一次性产生的，而是逐步渐进买入和卖出。计算BBAND，检查价格是否超过BBAND的上轨或下轨：<br />1，当价格大于上轨后，每天产生10%的比例买入交易信号<br />2，当价格低于下轨后，每天产生33%的比例卖出交易信号 |
| sarext    | `TimingSAREXT` | 扩展抛物线SAR策略，当指标大于0时发出买入信号，当指标小于0时发出卖出信号                                                                                                                       |
| ssma      | `SCRSSMA` | 单均线交叉策略——SMA均线(简单移动平均线)：根据股价与SMA均线的相对位置设定持仓比例                                                                                                                |
| sdema     | `SCRSDEMA` | 单均线交叉策略——DEMA均线(双重指数平滑移动平均线)：根据股价与DEMA均线的相对位置设定持仓比例                                                                                                          |
| sema      | `SCRSEMA` | 单均线交叉策略——EMA均线(指数平滑移动均线)：根据股价与EMA均线的相对位置设定持仓比例                                                                                                               |
 | ...       | ...     | 完整的内置策略清单请见[参考文档](../references/4-build-in-strategy-blender.md)                                                                                                                                              |



如果需要查看每一个内置交易策略的详细解释，例如策略参数的含义、信号生成规则，可以查看每一个交易策略的Doc-string：

例如：

```python
qt.built_ins('Crossline')
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

在ipython等交互式python环境中，也可以使用?来显示内置交易策略的详细信息，例如：

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

不过，在一个Operator对象中，不同策略生成的交易信号可能运行的交易价格是不同的，例如，某些策略生成开盘价交易信号，而另一些策略生成的是收盘价交易策略，那么不同的交易价格信号当然不应该混合。但除此之外，只要是交易价格相同的信号，都应该全部混合。

交易信号的混合即交易信号的各种运算或函数，从简单的逻辑运算、加减运算一直到复杂的自定义函数，只要能够应用于一个ndarray的函数，理论上都可以用于混合交易信号，只要最终输出的交易信号有意义即可。
### 定义策略组合方式`blender`

`qteasy`中的组合策略是由`blender`实现的。在一个`Operator`中，如果策略的数量多于1个，就必须定义一个`blender`。如果没有明确定义`blender`，而策略的数量超过1个时，`qteasy`会在运行`Operator`的时候创建一个默认的`blender`，但是为了让多重策略正确运行，用户需要自行定义`blender`。

`blender expression`是用户自行定义的一个组合表达式，用户使用这个表达式确定不同交易策略的组合方式。这个组合表达式使用四则运算符、逻辑运算符、函数等符号规定策略信号是如何组合的。`blender`表达式中可以包括以下元素：

`blender`表达式中支持的函数如下：

| 元素       |  示例   | 说明                                                         |
| :--------- | :-----: | :----------------------------------------------------------- |
| 策略序号   |  `s1`   | 以s开头，数字结尾的字符串，数字为`Operator`中的策略的序号，代表这个策略生成的交易信号 |
| 数字       | `-1.35` | 任何合法的数字，参与表达式运算的数字                         |
| 运算符     |   `+`   | 包括`'+-*/^'`等四则运算符                                    |
| 逻辑运算符 |  `and`  | 支持`'&|~'`以及`'and/or/not'`形式的逻辑运算符                |
| 函数       | `sum()` | 支持的函数参见后表                                           |
| 括号       |  `()`   | 组合运算                                                     |


### `blender`示例

当一个`Operator`对象中有三个交易策略时（其序号分别为0/1/2），按照以下方式定义的`blender`都是合法可用的，同时使用`Operator.set_blender()`来设置`blender`：

#### 使用四则运算符定义blender表达式

`'s0 + s1 + s2'`

此时三个交易策略生成的交易信号会被加起来，成为最终的交易信号，如果策略0的结果为买入10%，策略1结果为买入10%，策略2结果为买入30%，则最终的结果为买入50%

#### 使用逻辑运算符定义blender表达式：

`'s0 and s1 and s2'`

表示只有当交易策略1、2、3都出现交易信号的时候，才会最终形成交易信号。如策略1的结果为买入，策略2结果为买入，而策略3没有交易信号，则最终的结果为没有交易信号。

#### blender表达式中还可以包含括号和一些函数：

`'max(s0, s1) + s2'`

表示策略1、2的结果中最大值与策略3的结果相加，成为最终交易信号。如果策略1的结果为买入10%，策略2结果为买入20%，策略3结果为买入30%，最终的结果为买入50%

#### blender 表达式中每个策略可以出现不止一次，也可以出现纯数字：

`'(0.5 * s0 + 1.0 * s1 + 1.5 * s2) / 3 * min(s0, s1, s2)'`

上面的blender表达式表示：首先计算三个策略信号的加权平均（权重分别为0.5、1.0、1.5），然后再乘以三个信号的最小值

#### blender 表达式中函数的操作参数在函数名中定义：

`'clip_-0.5_0.5(s0 + s1 + s2) + pos_2_0.2(s0, s1, s2)'`

上面的blender表达式定义了两种不同的函数操作，分别得到结果后相加得到最终结果。第一个函数是范围剪切，将三组策略信号相加后，剪切掉小于-0.5的信号值以及大于0.5的信号值，得到计算结果；第二个函数是仓位判断函数，统计三组信号中持仓大于0.2的时间段，将其定义为“多头”，然后再统计每一个时间段三个策略中持多头建议的数量，如果超过两个策略持多头建议，则输出满仓多头，否则输出空仓。

blender表达式中支持的函数如下：

| 函数     |          表达式          | 说明                                                         |
| :------- | :----------------------: | :----------------------------------------------------------- |
| abs      |     `abs(*signals)`      | 绝对值函数<br />计算所有交易信号的绝对值<br />输入信号的数量不限 |
| avg      |     `avg(*signals)`      | 平均值函数<br />计算所有交易信号的平均值<br />输入信号的数量不限 |
| avgpos   |  `avgpos_N_T(*signals)`  | 平均值累计函数<br />当交易信号为持仓目标信号时，统计同一时间产生非空仓信号（输出信号绝对值>T）的个数，当空头/多头信号的数量大于N时，输出所有空头/多头信号的平均值，否则输出0.<br />输入信号的数量不限 |
| ceil     |      `ceil(signal)`      | 向上取整函数<br />交易信号向上取整<br />只能输入一个交易信号 |
| clip     |    `clip_U_L(signal)`    | 范围剪切函数<br />剪切超过范围的信号值，剪切上下范围在函数名中定义<br />只能输入一个交易信号 |
| combo    |    `combo(*signals)`     | 组合值函数<br />输出所有交易信号加总的值<br />输入信号的数量不限 |
| committee   |   `cmt_N_T(*signals)`    | 委员会函数（等同于累计持仓函数））<br />当交易信号为持仓目标信号时，统计同一时间产生非空仓信号（输出信号绝对值>T）的个数数，当多头/空头信号的数量大于N时，输出-1/1，否则输出0.<br />输入信号的数量不限 |
| exp      |      `exp(signal)`       | exp函数<br />计算e的信号次幂<br />只能输入一个交易信号       |
| floor    |     `floor(signal)`      | 向下取整函数<br />交易信号向下取整<br />只能输入一个交易信号 |
| log      |      `log(signal)`       | 对数函数<br />计算以e为底的对数值<br />只能输入一个交易信号  |
| log10    |     `log10(signal)`      | 以10为底的对数函数<br />计算以10为底的对数值<br />只能输入一个交易信号 |
| max      |     `max(*signals)`      | 最大值函数<br />计算所有交易信号的最大值<br />输入信号的数量不限 |
| min      |     `min(*signals)`      | 最小值函数<br />计算所有交易信号的最小值<br />输入信号的数量不限 |
| pos      |   `pos_N_T(*signals)`    | 累计持仓函数<br />当交易信号为持仓目标信号时，统计同一时间产生非空仓信号（输出信号绝对值>T）的个数数，当多头/空头信号的数量大于N时，输出-1/1，否则输出0.<br />输入信号的数量不限 |
| position | `position_N_T(*signals)` | 累计持仓函数<br />当交易信号为持仓目标信号时，统计同一时间产生非空仓信号（输出信号绝对值>T）的个数数，当多头/空头信号的数量大于N时，输出-1/1，否则输出0.<br />输入信号的数量不限 |
| pow      |     `pow(*signals)`      | 幂函数<br />计算第一个交易信号的第二个信号次幂即sig0^sig1<br />输入信号的数量只能为两个 |
| power    |    `power(*signals)`     | 幂函数<br />计算第一个交易信号的第二个信号次幂即sig0^sig1<br />输入信号的数量只能为两个 |
| sqrt     |      `sqrt(signal)`      | 平方根函数<br />交易信号的平方根<br />只能输入一个交易信号   |
| str      |    `str_T(*signals)`     | 强度累计函数<br />将所有交易信号加总，当信号强度超过T时，输出1，否则输出0<br />输入信号的数量不限 |
| strength |  `strength_T(*signals)`  | 强度累计函数<br />将所有交易信号加总，当信号强度超过T时，输出1，否则输出0<br />输入信号的数量不限 |
| sum      |     `sum(*signals)`      | 组合值函数<br />输出所有交易信号加总的值<br />输入信号的数量不限 |
| unify    |     `unify(signal)`      | 均一化函数<br />均一化交易信号，等比缩放同一行的交易信号使每一行的总和为1<br />只能输入一个交易信号 |
| vote    |   `vote_N_T(*signals)`    | 委员会投票函数（等同于累计持仓函数）<br />当交易信号为持仓目标信号时，统计同一时间产生非空仓信号（输出信号绝对值>T）的个数数，当多头/空头信号的数量大于N时，输出-1/1，否则输出0.<br />输入信号的数量不限 |


以下方法可以被用来设置或获取策略的blender

### `operator.set_blender(blender=None, price_type=None)`
设置blender，直接传入一个表达式，这个表达式会被自动解析后用于组合交易策略。


### `operator.view_blender()`
查看blender

### blender使用示例

下面使用一个例子来演示blender的工作方式：

```python
# 创建一个交易员对象，同时运行五个相同的dma交易策略，这些交易策略运行方式相同，但是设置不同的参数后，会产生不同的交易信号。我们通过不同的策略组合方式，得到不同的回测结果
op = qt.Operator('dma, dma, dma, dma, dma')
# 分别给五个不同的交易策略设置不同的策略参数，使他们产生不同的交易信号
op.set_parameter(stg_id=0, pars=(132, 200, 24))
op.set_parameter(stg_id=1, pars=(124, 187, 51))
op.set_parameter(stg_id=2, pars=(103, 81, 16))
op.set_parameter(stg_id=3, pars=(48, 111, 148))
op.set_parameter(stg_id=4, pars=(104, 127, 58))

# 第一种组合方式：加权平均方式：分别给每一个不同的策略设置不同的权重：
# s0: 权重0.8
# s0: 权重1.2
# s0: 权重2.0
# s0: 权重0.5
# s0: 权重1.5
# 将五个交易策略生成的交易信号加权平均后得到最终的交易信号
op.set_blender('(0.8*s0+1.2*s1+2*s2+0.5*s3+1.5*s4)/5')

# 运行策略
res = qt.run(op, mode=1)
# 得到结果如下：年化收益12.19，夏普率1.053
```

         ====================================
         |                                  |
         |       BACK TESTING RESULT        |
         |                                  |
         ====================================
    
    qteasy running mode: 1 - History back testing
    time consumption for operate signal creation: 130.5ms
    time consumption for operation back looping:  523.8ms
    
    investment starts on      2016-04-05 00:00:00
    ends on                   2021-02-01 00:00:00
    Total looped periods:     4.8 years.
    
    -------------operation summary:------------
    
              Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
    000300.SH   478      421    899   89.7%      0.0%     10.3%   
    
    Total operation fee:     ¥    2,615.40
    total investment amount: ¥  100,000.00
    final value:              ¥  174,263.46
    Total return:                    74.26% 
    Avg Yearly return:               12.19%
    Skewness:                         -0.31
    Kurtosis:                         10.31
    Benchmark return:                65.96% 
    Benchmark Yearly return:         11.06%
    
    ------strategy loop_results indicators------ 
    alpha:                            0.007
    Beta:                             1.408
    Sharp ratio:                      1.053
    Info ratio:                       0.000
    250 day volatility:               0.111
    Max drawdown:                    12.26% 
        peak / valley:        2019-04-19 / 2020-02-03
        recovered on:         2020-07-06
    ===========END OF REPORT=============




![png](../references/img/output_10_1.png)
    



```python
# 第二种组合方式：将五个交易策略看成一个“委员会”，最终的持仓仓位由委员会投票决定：
# 当同一时间累计五个策略中至少三个输出多头满仓使，输出多头满仓，否则空仓
op.set_blender('pos_3_0(s0, s1, s2, s3, s4)')
# 运行策略
res = qt.run(op, mode=1)
# 得到结果如下：年化收益13.39，夏普率1.075
```


         ====================================
         |                                  |
         |       BACK TESTING RESULT        |
         |                                  |
         ====================================
    
    qteasy running mode: 1 - History back testing
    time consumption for operate signal creation: 540.1ms
    time consumption for operation back looping:  435.8ms
    
    investment starts on      2016-04-05 00:00:00
    ends on                   2021-02-01 00:00:00
    Total looped periods:     4.8 years.
    
    -------------operation summary:------------
    
              Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
    000300.SH    11       10     21   55.4%      0.0%     44.6%   
    
    Total operation fee:     ¥      585.88
    total investment amount: ¥  100,000.00
    final value:              ¥  183,485.41
    Total return:                    83.49% 
    Avg Yearly return:               13.39%
    Skewness:                         -0.43
    Kurtosis:                         14.75
    Benchmark return:                65.96% 
    Benchmark Yearly return:         11.06%
    
    ------strategy loop_results indicators------ 
    alpha:                            0.046
    Beta:                             1.003
    Sharp ratio:                      1.075
    Info ratio:                       0.006
    250 day volatility:               0.124
    Max drawdown:                    15.71% 
        peak / valley:        2019-04-19 / 2020-02-03
        recovered on:         2020-07-31
    ===========END OF REPORT=============




![png](../references/img/output_11_1.png)
    



```python
# 第三种组合方式：同样是委员会策略，但输出满仓多头的投票门槛变为2票，即只要有两个策略认为输出多头即可
op.set_blender('pos_2_0(s0, s1, s2, s3, s4)')
# 运行策略
res = qt.run(op, mode=1)
# 得到结果如下：年化收益12.88，夏普率0.824
```


         ====================================
         |                                  |
         |       BACK TESTING RESULT        |
         |                                  |
         ====================================
    
    qteasy running mode: 1 - History back testing
    time consumption for operate signal creation: 133.8ms
    time consumption for operation back looping:  500.0ms
    
    investment starts on      2016-04-05 00:00:00
    ends on                   2021-02-01 00:00:00
    Total looped periods:     4.8 years.
    
    -------------operation summary:------------
    
              Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
    000300.SH    15       14     29   71.4%      0.0%     28.6%   
    
    Total operation fee:     ¥      707.30
    total investment amount: ¥  100,000.00
    final value:              ¥  179,532.76
    Total return:                    79.53% 
    Avg Yearly return:               12.88%
    Skewness:                         -0.45
    Kurtosis:                         10.45
    Benchmark return:                65.96% 
    Benchmark Yearly return:         11.06%
    
    ------strategy loop_results indicators------ 
    alpha:                            0.029
    Beta:                             1.000
    Sharp ratio:                      0.824
    Info ratio:                       0.007
    250 day volatility:               0.144
    Max drawdown:                    15.94% 
        peak / valley:        2018-01-24 / 2019-01-03
        recovered on:         2019-02-25
    ===========END OF REPORT=============




![png](../references/img/output_12_1_2.png)
    