# QTEASY使用教程03——创建交易策略并评价回测结果

创建交易策略，并且使用历史数据回溯测试交易策略的交易结果，并对交易结果进行评价是qteasy的核心功能之一。
qteasy通过一个交易员对象（Operator）汇总一系列的交易策略，并且通过qt.run()函数在一段设定好的历史时间段内模拟交易策略的运行，生成交易信号，使用历史价格进行模拟交易，生成交易结果，计算评价指标，并以可视化形式输出为图表。

本章节以一个最常见的基金择时投资策略为例子，演示了以下内容：
- 创建一个简单的dma择时投资策略，创建一个交易员对象使用这个策略，演示如何修改、添加策略
- 通过`qt.configure()`设置相关的环境变量，使用过去10年的沪深300指数历史数据，回测策略表现
- 通过对过去10年左右的沪深300指数历史数据，对策略进行参数寻优，最终演示寻优后的结果

首先我们导入qteasy模块
为了在线打印图表，使用`matplotlib inline`设置图表打印模式为在线打印


```python
import sys
sys.path.append('../')
import qteasy as qt
%matplotlib inline
```


## 创建Strategy对象和Operator对象
qteasy中的每一个交易策略都被定义为交易策略（Strategy）对象。每个交易对象包含了一系列的交易规则，这些规则包括三个方面：
1. **策略运行规则**，包括策略运行的频率，所使用的历史数据类型，历史数据窗口长度，定义了策略如何运行以及如何使用历史数据
2. **信号生成规则**，交易信号的生成规则，即如何根据相关历史数据生成何种交易信号，这是交易策略的核心
3. **交易信号类型**，交易信号的不同类型决定了模拟交易模块如何处理交易信号

在qteasy中，交易策略是由交易员对象（Operator）执行的，同一时间只能有一个Operator对象在运行，但是同一个交易员可以同时执行一个或多个交易策略，这些交易策略可以针对同一个投资组合进行交易，用户可以定义特定的“混合”方法，把多个简单交易策略混合成为一个复杂交易策略运行。

### 创建Strategy对象

创建Strategy对象的最简单方法是使用qt.built_in模块, 也可以在创建Operator对象的时候同时创建。

```python
# 通过qt内置策略模块创建一个DMA则时策略
stg = qt.built_in.DMA()
# 通过stg.info()可以查看策略的主要信息：
stg.info()
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



从上面的输出可以看到这个交易策略的基本信息。除了名称、描述以外，比较重要的信息包括：

- **策略参数 Strategy Parameter**。策略参数是策略运行过程中所需的外部参数，根据策略规则的不同，策略使用的参数也不同，这些参数对策略的运行过程产生影响，不同的参数会影响策略的输出。例如，在双均线则时策略中，长均线的计算周期和短均线的计算周期就是两个策略参数。
- **参数类型/范围 Parameter Types / Range**: 不同的策略参数会极大地影响一个策略的最终结果，设置好参数的取值范围和类型之后，qteasy可以通过不同方法在参数空间内搜索最佳参数，使策略的性能达到最佳。
- **策略数据频率和运行频率 Data Frequcney / Sample Frequency**。策略运行的频率以及所需数据的频率，例如每周执行一次，每月执行一次或每分钟执行一次等等，一般来说数据频率与执行频率相关
- **数据类型 Data Types**：运行策略所需要读取的历史数据类型。对DMA策略来说，仅需要收盘价即可。

### 创建Operator对象

使用`qt.Operator()`可以创建`Operator`对象。

###  `qt.Operator(strategies=None, signal_type=None, op_type=None)`

创建一个Operator对象，用于操作所有的交易策略。


```python
op = qt.Operator()
```

    OPERATOR INFO:
    =========================
    Information of the Module
    =========================
    Total 0 operation strategies, requiring 0 types of historical data:
    
    0 types of back test price types:
    []


交易员对象是一个策略容器，在一个Operator对象中可以添加任意多个交易策略，同时，在Operator对象中，可以管理交易策略的混合方式(blender)，交易信号的处理方式以及交易运行的方式。

常用的Operator属性及方法如下：

### 获取Operator对象的基本信息

### `op.info()`
打印Operator对象的重要信息

### `op.strategies`
获取Operator对象中所有交易策略的清单

### `op.strategy_ids`
获取Operator对象中所有交易策略的ID

### `op.strategy_count`
获取Operator对象中交易策略的数量

### `op.signal_type`
Operator对象的信号类型，代表交易信号的含义及处理方式：
- **'pt': 目标持仓比例信号**，在这个模式下，交易员关注一个投资组合中各个成份股票的持仓比例，通过适时的买入和买出，维持各个成份股的持仓比例在一个目标值上；
- **'ps': 百分比交易信号**，在这个模式下，交易员关注定时产生的比例交易信号，根据交易信号按比例买入或买出股票
- **'vs': 数量交易信号**，在这个模式下，交易员关注定时产生的交易信号，按照交易信号买入或买出一定数量的股票

### `op.op_type`
Operator对象的运行模式：
- 'batch': 批量运行模式，在回测模式或优化模式下，预先生成交易清单，再批量进行模拟交易，运行速度较快
- 'realtime': 实时运行模式，生成交易信号立即模拟交易，产生模拟交易结果后，再进行下一次交易信号生成，适用于实时运行模式，或特殊情况下的回测模式

### 获取交易策略

### `op.get_stg(stg_id)`
通过策略ID获取策略对象，下面的方法效果相同，且可以通过数字序号来获取策略
```
stg = op.get_stg(stg_id)
stg = op[stg_id] 
stg = op[stg_idx]
```
### 添加或修改交易策略

### `op.add_strategy(stg, **kwargs)`
添加一个策略到Operator，添加策略的同时可以同时设置策略参数

### `op.add_strategies(strategies)`
批量添加一系列策略到Operator，添加的同时不能同时设置策略参数

### `op.remove_strategy(id_or_pos=None)`
从Operator中删除一个策略

### `op.clear_strategies()`
清除Operator中的所有交易策略

### 设置策略参数或Operator参数

### `op.set_parameter(stg_id, pars=None, opt_tag=None, par_range=None, par_types=None, data_freq=None, strategy_run_freq=None, window_length=None, data_types=None, strategy_run_timing=None, **kwargs)`
指定一个交易策略的ID，设置这个交易策略的策略参数或其他属性

### `op.set_blender(price_type=None, blender=None)` 
设置交易策略的混合方式。当Operator中有多个交易策略时，每个交易策略分别运行生成多组交易信号，再按照用户定义的规则混合后输出一组交易信号，用于交易

我们可以用下面的代码将刚创建的DMA策略加入到Operator中去，并设置必要的策略参数

所有的参数设置都可以使用`operator.set_parameter`方法，可以同时传入多个参数
通过设置策略的`opt_tag`可以控制策略是否参与优化，而`par_range`参数定义了策略优化时需要用到的参数空间
在此时我们并不知道对于过去15年的沪深300指数来说，最优的DMA择时参数是什么，因此可以输入几个随机的参数，进行一次回测，看看结果如何


```python
op.clear_strategies()
op.add_strategy(stg, pars=(26, 35, 189), opt_tag=1)
print(f'Operator strategies: {op.strategies}')
print(f'Strategy IDs are: {op.strategy_ids}')
op.info(verbose=True)
```

    Operator strategies: [RULE-ITER(DMA)]
    Strategy IDs are: ['custom']
    OPERATOR INFO:
    =========================
    Information of the Module
    =========================
    Total 1 operation strategies, requiring 1 types of historical data:
    close
    1 types of back test price types:
    ['close']
    for backtest histoty price type - close: 
    [RULE-ITER(DMA)]:
    no blender
    Parameters of GeneralStg Strategies:
    Strategy_type:      RuleIterator
    Strategy name:      DMA
    Description:        Quick DMA strategy, determine long/short position according to differences of moving average prices with simple timing strategy
    Strategy Parameter: (26, 35, 189)
    
    Strategy Properties     Property Value
    ---------------------------------------
    Parameter count         3
    Parameter types         ['int', 'int', 'int']
    Parameter range         [(10, 250), (10, 250), (10, 250)]
    Data frequency          d
    Sample frequency        d
    Window length           270
    Data types              ['close']
    
    =========================


### 配置qteasy的回测参数

Operator对象创建好并添加策略后就可以开始进行回测了

qteasy提供了丰富的环境参数以控制回测的具体过程
所有的环境参数变量值都可以通过`qt.Configuration()`查看，并通过`qt.Configure()`来设置。

### `qt.configuration()`
查看qteasy运行环境变量

### `qt.configure()`
设置qteasy运行环境变量

与回测相关的主要环境变量参数包括：

- 回测交易的目标股票/指数
- 回测交易的起止时间段
- 回测交易的初始投资金额
- 回测交易的交易费用和交易规则
- 交易结果评价的基准指数

以上所有回测交易参数都可以通过`qt.configure()`设置:


```python
qt.configure(
    mode=1,  # 设置运行模式为：1-回测模式
    benchmark_asset = '000300.SH',  # 设置交易评价基准
    benchmark_asset_type = 'IDX',  # 设置交易评价基准的资产类型
    asset_pool = '000300.SH',  # 设置交易资产组合
    asset_type = 'IDX',  # 交易资产组合的资产类型
    trade_batch_size = 0,  # 设置允许最小交易批量
    invest_start = '20100105',  # 设置交易开始日期
    invest_end = '20201231',  # 设置交易终止日期
    invest_cash_amounts = [1000000],  # 设置初始交易投资金额为十万元
    visual=True  # 输出可视化交易结果图表
)
```

### 启动qteasy并开始运行Operator

### `qt.run(operator, **config)`
开始运行Operator，根据运行的mode，qteasy会进入到不同的运行模式，输出不同的结果：

- **mode 0 实时模式**：读取最近的（实时）数据，生成当前最新的交易信号。再此模式下，可以设置qteasy定期执行，定期读取最新数据，定期生成实时交易信号
- **mode 1 回测模式**：读取过去一段时间内的历史数据，使用该数据生成交易信号并模拟交易，输出模拟交易的结果
- **mode 2 优化模式**：读取过去一段时间内的历史数据，通过反复运行同一套交易策略但使用不同的参数组合，搜索在这段时间内表现最佳的策略参数

只要运行`qteasy.run(operator, **config)`就可以开始运行Operator了，其中`**config`是测试环境参数，在qt.run()中以参数形式传入的环境变量仅仅在本次运行中有效，但是在qt.configure()中设置的环境变量将一直有效，直到下次改变为止


回测最终资产为19万元，年化收益率只有4.83%，夏普率只有0.0783，收益率低于同期沪深300指数


```python
qt.run(op)
```

运行qteasy后，系统会自动读取历史数据，进行回测，完成结果评价并打印回测报告。

回测报告会包含以下信息：

- 回测计算耗时
- 回测区间开始日期及结束日期、持续时间等信息
- 交易统计信息：如买入次数、卖出次数，满仓比例，空仓比例、总交易费用等
- 收益信息：初始投资额，最终资产额，总收益率，年化收益率，基准总收益率，基准年化收益率，收益率的峰度和偏度
- 投资组合评价指标：Alpha，Beta、夏普率、信息比率、波动率以及最大回撤


         ====================================
         |                                  |
         |       BACK TESTING RESULT        |
         |                                  |
         ====================================
    
    qteasy running mode: 1 - History back testing
    time consumption for operate signal creation: 1s 164.2ms
    time consumption for operation back looping:  6s 720.2ms
    
    investment starts on      2010-01-05 00:00:00
    ends on                   2020-12-31 00:00:00
    Total looped periods:     11.0 years.
    
    -------------operation summary:------------
    
              Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
    000300.SH    53       53    106   54.0%      0.0%     46.0%   
    
    Total operation fee:     ¥   20,382.34
    total investment amount: ¥1,000,000.00
    final value:              ¥1,052,696.57
    Total return:                     5.27% 
    Avg Yearly return:                0.47%
    Skewness:                         -0.76
    Kurtosis:                         11.44
    Benchmark return:                46.22% 
    Benchmark Yearly return:          3.52%
    
    ------strategy loop_results indicators------ 
    alpha:                           -0.047
    Beta:                             1.000
    Sharp ratio:                     -0.077
    Info ratio:                      -0.018
    250 day volatility:               0.156
    Max drawdown:                    46.12% 
        peak / valley:        2010-11-08 / 2014-06-19
        recovered on:         2015-04-17
     
    ===========END OF REPORT=============

除了回测报告以外，一张可视化图表也会被打印出来，显示整个回测过程的详细信息。

在这张信息图中，会显示以下信息：

- 整个回测历史的收益率曲线图（同时显示持仓区间、卖卖点、基准收益率曲线和最大回撤区间）
- 对数比例收益率曲线和基准收益率对比图
- 每日收益变动图
- 滚动夏普率和alpha率变动图（投资组合盈利能力评价）
- 滚动波动率（Volatility）和Beta率变动图（投资组合风险评价）
- 历史回撤分析图（潜水图）
- 月度、年度收益率热力图和条形图
- 月度收益率统计频率直方图


![png](img/output_12_2.png)
    


### 单择时策略的优化
显然，没有经过优化的参数无法得到理想的回测结果，因此我们需要进行一次优化

通过设置context对象的各个参数，我们可以设置优化方式并控制优化过程：
以下参数的含义分别如下：

- 优化方法设置为1，使用蒙特卡洛优化，对于较大的参数空间有较好的寻优能力
- 输出结果数量设置为30
- 优化过程迭代次数为1000次
- parallel参数设置为True会使用多核处理器的所有核心进行并行计算节省时间

最后开始优化，使用`perfs_dma`和`pars_dma`两个变量来存储优化结果
优化过程中会显示进度条，结束后会显示优化结果


```python
pars_dma = qt.run(op, 
                  mode=2,
                  opti_method=1,
                  opti_sample_count=1000,
                  opti_start='20101231',
                  opti_end='20201231',
                  opti_cash_dates='20101231',
                  test_start='20101231',
                  test_end='20201231',
                  test_cash_dates='20101231',
                  parallel=True)
print(f'optimization completed, 50 parameters found, they are\n'
      f'{pars_dma}')
```



    [########################################]1000/1000-100.0%  best performance: 340613.629
    Optimization completed, total time consumption: 38"247
    [########################################]30/30-100.0%  best performance: 340613.629
    ==================================== 
    |                                  |
    |       OPTIMIZATION RESULT        |
    |                                  |
    ====================================
    
    qteasy running mode: 2 - Strategy Parameter Optimization
    
    investment starts on 2010-12-31 00:00:00
    ends on 2020-12-31 00:00:00
    Total looped periods: 10.0 years.
    total investment amount: ¥   100,000.00
    Reference index type is 000300.SH at IDX
    Total Benchmark rtn: 66.59% 
    Average Yearly Benchmark rtn rate: 5.23%
    statistical analysis of optimal strategy messages indicators: 
    total return:        161.24% ± 29.73%
    annual return:       10.01% ± 1.18%
    alpha:               0.048 ± 0.014
    Beta:                1.001 ± 0.001
    Sharp ratio:         0.625 ± 0.089
    Info ratio:          0.013 ± 0.004
    250 day volatility:  0.151 ± 0.006
    other messages indicators are listed in below table
    
        Strategy items  Sell-outs Buy-ins ttl-fee      FV      ROI   Benchmark rtn  MDD 
    0    (147, 157, 57)    25.0     25.0  1,213.16 231,710.13 131.7%     66.6%     38.1%
    1    (88, 108, 127)    16.0     15.0  1,009.93 233,554.10 133.6%     66.6%     44.3%
    2    (105, 160, 29)    21.0     20.0  1,344.78 232,247.09 132.2%     66.6%     26.4%
    3    (149, 194, 24)    19.0     19.0  1,062.61 233,932.11 133.9%     66.6%     33.4%
    4    (105, 185, 25)    18.0     17.0  1,094.07 236,171.54 136.2%     66.6%     40.6%
    5    (86, 147, 107)    11.0     10.0    668.08 234,827.39 134.8%     66.6%     39.7%
    6    (88, 157, 101)    11.0     10.0    715.01 236,851.09 136.9%     66.6%     31.6%
    7    (144, 181, 57)    19.0     19.0  1,093.20 240,445.16 140.4%     66.6%     33.8%
    8     (94, 165, 78)    12.0     11.0    724.66 240,825.90 140.8%     66.6%     38.1%
    9    (68, 113, 142)    13.0     12.0    819.42 244,805.70 144.8%     66.6%     42.5%
    10     (80, 64, 57)    30.0     30.0  1,767.04 245,084.54 145.1%     66.6%     28.8%
    11   (101, 124, 65)    23.0     22.0  1,726.89 245,504.45 145.5%     66.6%     30.7%
    12   (150, 189, 33)    20.0     20.0  1,142.62 246,185.41 146.2%     66.6%     34.3%
    13   (119, 200, 30)    12.0     11.0    705.66 248,111.42 148.1%     66.6%     24.1%
    14   (52, 111, 136)    14.0     13.0    810.29 254,764.49 154.8%     66.6%     40.5%
    15    (55, 151, 87)    14.0     13.0    896.37 248,370.33 148.4%     66.6%     38.2%
    16    (98, 129, 45)    22.0     21.0  1,480.50 252,764.13 152.8%     66.6%     37.1%
    17    (101, 59, 50)    27.0     26.0  1,505.08 255,487.88 155.5%     66.6%     28.8%
    18   (179, 240, 25)    19.0     19.0  1,149.62 259,380.09 159.4%     66.6%     33.8%
    19   (82, 127, 144)    12.0     11.0    810.46 268,321.59 168.3%     66.6%     37.4%
    20   (44, 135, 117)    13.0     12.0    741.60 268,837.16 168.8%     66.6%     42.6%
    21   (103, 127, 57)    22.0     21.0  1,628.33 269,776.04 169.8%     66.6%     30.3%
    22   (128, 152, 92)    15.0     15.0    883.81 272,170.16 172.2%     66.6%     32.6%
    23    (91, 198, 13)    17.0     16.0  1,209.55 277,214.25 177.2%     66.6%     43.3%
    24  (102, 110, 129)    26.0     25.0  2,056.58 311,876.36 211.9%     66.6%     33.4%
    25   (129, 204, 16)    14.0     14.0    840.49 279,142.60 179.1%     66.6%     32.6%
    26    (90, 185, 45)    11.0     10.0    735.84 279,320.37 179.3%     66.6%     40.6%
    27  (104, 111, 107)    30.0     29.0  2,207.23 317,371.14 217.4%     66.6%     41.0%
    28   (101, 150, 24)    23.0     22.0  2,012.97 331,442.65 231.4%     66.6%     26.4%
    29   (104, 142, 87)    15.0     14.0  1,044.25 340,613.63 240.6%     66.6%     23.5%
    
    ===========END OF REPORT=============
    
    [########################################]30/30-100.0%  best performance: 340613.629
    ==================================== 
    |                                  |
    |       OPTIMIZATION RESULT        |
    |                                  |
    ====================================
    
    qteasy running mode: 2 - Strategy Parameter Optimization
    
    investment starts on 2010-12-31 00:00:00
    ends on 2020-12-31 00:00:00
    Total looped periods: 10.0 years.
    total investment amount: ¥   100,000.00
    Reference index type is 000300.SH at IDX
    Total Benchmark rtn: 66.59% 
    Average Yearly Benchmark rtn rate: 5.23%
    statistical analysis of optimal strategy messages indicators: 
    total return:        161.24% ± 29.73%
    annual return:       10.01% ± 1.18%
    alpha:               0.048 ± 0.014
    Beta:                1.001 ± 0.001
    Sharp ratio:         0.625 ± 0.089
    Info ratio:          0.013 ± 0.004
    250 day volatility:  0.151 ± 0.006
    other messages indicators are listed in below table
    
        Strategy items  Sell-outs Buy-ins ttl-fee      FV      ROI   Benchmark rtn  MDD 
    0    (105, 160, 29)    21.0     20.0  1,344.78 232,247.09 132.2%     66.6%     26.4%
    1    (88, 108, 127)    16.0     15.0  1,009.93 233,554.10 133.6%     66.6%     44.3%
    2    (147, 157, 57)    25.0     25.0  1,213.16 231,710.13 131.7%     66.6%     38.1%
    3    (105, 185, 25)    18.0     17.0  1,094.07 236,171.54 136.2%     66.6%     40.6%
    4    (88, 157, 101)    11.0     10.0    715.01 236,851.09 136.9%     66.6%     31.6%
    5    (149, 194, 24)    19.0     19.0  1,062.61 233,932.11 133.9%     66.6%     33.4%
    6    (144, 181, 57)    19.0     19.0  1,093.20 240,445.16 140.4%     66.6%     33.8%
    7    (86, 147, 107)    11.0     10.0    668.08 234,827.39 134.8%     66.6%     39.7%
    8    (68, 113, 142)    13.0     12.0    819.42 244,805.70 144.8%     66.6%     42.5%
    9     (94, 165, 78)    12.0     11.0    724.66 240,825.90 140.8%     66.6%     38.1%
    10   (150, 189, 33)    20.0     20.0  1,142.62 246,185.41 146.2%     66.6%     34.3%
    11   (101, 124, 65)    23.0     22.0  1,726.89 245,504.45 145.5%     66.6%     30.7%
    12     (80, 64, 57)    30.0     30.0  1,767.04 245,084.54 145.1%     66.6%     28.8%
    13   (119, 200, 30)    12.0     11.0    705.66 248,111.42 148.1%     66.6%     24.1%
    14    (55, 151, 87)    14.0     13.0    896.37 248,370.33 148.4%     66.6%     38.2%
    15    (98, 129, 45)    22.0     21.0  1,480.50 252,764.13 152.8%     66.6%     37.1%
    16   (52, 111, 136)    14.0     13.0    810.29 254,764.49 154.8%     66.6%     40.5%
    17    (101, 59, 50)    27.0     26.0  1,505.08 255,487.88 155.5%     66.6%     28.8%
    18   (179, 240, 25)    19.0     19.0  1,149.62 259,380.09 159.4%     66.6%     33.8%
    19   (82, 127, 144)    12.0     11.0    810.46 268,321.59 168.3%     66.6%     37.4%
    20   (44, 135, 117)    13.0     12.0    741.60 268,837.16 168.8%     66.6%     42.6%
    21   (103, 127, 57)    22.0     21.0  1,628.33 269,776.04 169.8%     66.6%     30.3%
    22   (128, 152, 92)    15.0     15.0    883.81 272,170.16 172.2%     66.6%     32.6%
    23    (91, 198, 13)    17.0     16.0  1,209.55 277,214.25 177.2%     66.6%     43.3%
    24   (129, 204, 16)    14.0     14.0    840.49 279,142.60 179.1%     66.6%     32.6%
    25    (90, 185, 45)    11.0     10.0    735.84 279,320.37 179.3%     66.6%     40.6%
    26  (104, 111, 107)    30.0     29.0  2,207.23 317,371.14 217.4%     66.6%     41.0%
    27  (102, 110, 129)    26.0     25.0  2,056.58 311,876.36 211.9%     66.6%     33.4%
    28   (101, 150, 24)    23.0     22.0  2,012.97 331,442.65 231.4%     66.6%     26.4%
    29   (104, 142, 87)    15.0     14.0  1,044.25 340,613.63 240.6%     66.6%     23.5%
    
    ===========END OF REPORT=============




![png](img/output_14_2.png)
    


    optimization completed, 50 parameters found, they are
    [(147, 157, 57), (105, 160, 29), (88, 108, 127), (149, 194, 24), (86, 147, 107), (105, 185, 25), (88, 157, 101), (144, 181, 57), (94, 165, 78), (68, 113, 142), (80, 64, 57), (101, 124, 65), (150, 189, 33), (119, 200, 30), (55, 151, 87), (98, 129, 45), (52, 111, 136), (101, 59, 50), (179, 240, 25), (82, 127, 144), (44, 135, 117), (103, 127, 57), (128, 152, 92), (91, 198, 13), (129, 204, 16), (90, 185, 45), (102, 110, 129), (104, 111, 107), (101, 150, 24), (104, 142, 87)]


优化结束后，可以看到三十组最佳参数，其中最差的一组也能实现最终资产6万元以上。我们可以手动选取其中最佳的参数，再进行一次回测：

能发现终值从上次回测的1.9万暴涨至12.4万，年化收益18.9%，夏普率也上升到了0.833


```python
op.set_parameter('dma', pars=(104, 142, 87))
qt.run(op,
      mode=1, visual=True)
```

输出回测结果如下：

         ====================================
         |                                  |
         |       BACK TESTING RESULT        |
         |                                  |
         ====================================
    
    qteasy running mode: 1 - History back testing
    time consumption for operate signal creation: 55.7ms
    time consumption for operation back looping:  885.7ms
    
    investment starts on      2010-12-31 00:00:00
    ends on                   2020-12-31 00:00:00
    Total looped periods:     10.0 years.
    
    -------------operation summary:------------
    
              Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
    000300.SH    15       14     29   52.6%      0.0%     47.4%   
    
    Total operation fee:     ¥    1,044.25
    total investment amount: ¥  100,000.00
    final value:              ¥  340,613.63
    Total return:                   240.61% 
    Avg Yearly return:               13.03%
    Skewness:                         -0.78
    Kurtosis:                         13.36
    Benchmark return:                66.59% 
    Benchmark Yearly return:          5.23%
    
    ------strategy loop_results indicators------ 
    alpha:                            0.087
    Beta:                             1.001
    Sharp ratio:                      0.751
    Info ratio:                       0.020
    250 day volatility:               0.140
    Max drawdown:                    23.53% 
        peak / valley:        2015-12-31 / 2016-01-28
        recovered on:         2017-08-28
    
    ===========END OF REPORT=============




![png](img/output_16_2.png)
    
## 创建一个自定义策略

使用qteasy不仅可以使用内置策略，也可以创建自定义策略。下面有一个简单的例子，定义了一个简单的轮动交易策略

