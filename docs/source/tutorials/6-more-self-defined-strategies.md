
# 创建自定义因子选股交易策略

`qteasy`是一个完全本地化部署和运行的量化交易分析工具包，具备以下功能：

- 金融数据的获取、清洗、存储以及处理、可视化、使用
- 量化交易策略的创建，并提供大量内置基本交易策略
- 向量化的高速交易策略回测及交易结果评价
- 交易策略参数的优化以及评价
- 交易策略的部署、实盘运行

通过本系列教程，您将会通过一系列的实际示例，充分了解`qteasy`的主要功能以及使用方法。

## 开始前的准备工作

在开始本节教程前，请先确保您已经掌握了下面的内容：

- **安装、配置`qteasy`** —— [QTEASY教程1](1-get-started.md)
- **设置了一个本地数据源**，并已经将足够的历史数据下载到本地——[QTEASY教程2](2-get-data.md)
- **学会创建交易员对象，使用内置交易策略**，——[QTEASY教程3](3-start-first-strategy.md)
- **学会使用混合器，将多个简单策略混合成较为复杂的交易策略**——[QTEASY教程4](4-build-in-strategies.md)
- **了解如何自定义交易策略**——[QTEASY教程5](5-first-self-defined-strategy.md)

在[QTEASY文档](https://qteasy.readthedocs.io/zh/latest/)中，还能找到更多关于使用内置交易策略、创建自定义策略等等相关内容。对`qteasy`的基本使用方法还不熟悉的同学，可以移步那里查看更多详细说明。

## 本节的目标

在本节中，我们将承接上一节开始的内容，介绍`qteasy`的交易策略基类，在介绍过一个最简单的择时交易策略类以后，我们将介绍如何使用`qteasy`提供的另外两种策略基类，创建一个多因子选股策略。

为了提供足够的使用便利性，`qteasy`的提供的各种策略基类本质上并无区别，只是为了减少用户编码工作量而提供的预处理形式，甚至可以将不同的交易策略基类理解成，为了特定交易策略设计的“语法糖”，因此，同一交易策略往往可以用多种不同的交易策略基类实现，因此，在本节中，我们将用两种不同的策略基类来实现一个Alpha选股交易策略。
## Alpha选股策略的选股思想

我们在这里讨论的Alpha选股策略是一个低频运行的选股策略，这个策略可以每周或者每月运行一次，每次选股时会遍历HS300指数的全部成分股，依照一定的标准将这300支股票进行优先级排序，从中选择出排位靠前的30支股票，等权持有，也就是说，每个月进行一次调仓换股，调仓时将排名靠后的股票卖掉，买入排名靠前的股票，并确保股票的持有份额相同。

Alpha选股策略的排名依据每一支股票的两个财务指标：EV（企业市场价值）以及EBITDA（息税折旧摊销前利润）来计算，对每一支股票计算EV与EBITDA的比值，当这个比值大于0的时候，说明该上市公司是盈利的（因为EBITDA为正）。这时，这个比值代表该公司每赚到一块钱利润，需要投入的企业总价值。自然，这个比值越低越好。例如，下面两家上市公司数据如下：

- A公司的EBITDA为一千万，而企业市场价值为一百亿，EV/EBITDA=1000.。说明该公司每一千元的市场价值可以挣到一元钱利润
- B公司的EBITDA同样为一千万，企业市场价值为一千亿，EV/EBITDA=10000，说明该公司每一万元的市场价值可以挣到一元钱利润

从常理分析，我们自然会觉得A公司比较好，因为靠着较少的公司市场价值，就挣到了同样的利润，这时我们认为A公司的排名比较靠前。

按照上面的规则，我们在每个月的最后一天，将HS300成分股的所有上市公司全部进行一次从小到大排名，剔除掉EV/EBITDA小于0的公司（盈利为负的公司当然应该剔除）以后，选择排名最靠前的30个公司持有，就是Alpha选股交易策略。

其实，类似于这样的指标排序选股策略，`qteasy`提供了一个内置交易策略可以直接实现：

```python
>>> import qteasy as qt
>>> qt.built_ins('finance')
 以股票过去一段时间内的财务指标的平均值作为选股因子选股
        基础选股策略。以股票的历史指标的平均值作为选股因子，因子排序参数可以作为策略参数传入
        改变策略数据类型，根据不同的历史数据选股，选股参数可以通过pars传入
    策略参数:
        - sort_ascending: enum, 是否升序排列因子
            - True: 优先选择因子最小的股票,
            - False, 优先选择因子最大的股票
        - weighting: enum, 股票仓位分配比例权重
            - 'even'       :默认值, 所有被选中的股票都获得同样的权重
            - 'linear'     :权重根据因子排序线性分配
            - 'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
            - 'proportion' :权重与股票的因子分值成正比
        - condition: enum, 股票筛选条件
            - 'any'        :默认值，选择所有可用股票
            - 'greater'    :筛选出因子大于ubound的股票
            - 'less'       :筛选出因子小于lbound的股票
            - 'between'    :筛选出因子介于lbound与ubound之间的股票
            - 'not_between':筛选出因子不在lbound与ubound之间的股票
        - lbound: float, 股票筛选下限值, 默认值np.-inf
        - ubound: float, 股票筛选上限值, 默认值np.inf
        - max_sel_count: float, 抽取的股票的数量(p>=1)或比例(p<1), 默认值：0.5，表示选中50%的股票
    信号类型:
        PT型：百分比持仓比例信号
    信号规则:
        使用data_types指定一种数据类型，将股票过去的datatypes数据取平均值，将该平均值作为选股因子进行选股
    策略属性缺省值:
        默认参数：(True, 'even', 'greater', 0, 0, 0.25)
        数据类型：eps 每股收益，单数据输入
        采样频率：年
        窗口长度：270
        参数范围：[(True, False),
        ('even', 'linear', 'proportion'),
        ('any', 'greater', 'less', 'between', 'not_between'),
        (-np.inf, np.inf),
        (-np.inf, np.inf),
        (0, 1.)]

    策略不支持参考数据，不支持交易数据
    
<class 'qteasy.built_in.SelectingAvgIndicator'>
```

不过这个内置交易策略仅支持以`qteasy`内置历史数据类型为选股因子，例如pe市盈率、profit利润等数据是`qteasy`的内置历史数据，可以直接引用。但如果是``qteasy``内置历史数据中找不到的选股因子，就不能直接使用内置交易策略了。EV/EBITDA这个指标是一个计算指标，因此，我们必须使用自定义交易策略。并在自定义策略中计算该指标。
## 计算选股指标

为了计算EV/EBITDA，我们必须至少先确认`qteasy`中是否已经提供了EV和EBITDA这两种历史数据：

我们可以使用`find_history_data()`来查看历史数据是否被`qteasy`支持
```python
>>> import qteasy as qt
>>> qt.find_history_data('ev')
matched following history data, 
use "qt.get_history_data()" to load these historical data by its data_id:
------------------------------------------------------------------------
Empty DataFrame
Columns: [freq, asset_type, table_name, description]
Index: []
========================================================================
[]
>>> qt.find_history_data('ebitda')
matched following history data, 
use "qt.get_history_data()" to load these historical data by its data_id:
------------------------------------------------------------------------
              freq asset      table                  desc
data_id                                                  
income_ebitda    q     E     income   上市公司利润表 - 息税折旧摊销前利润
ebitda           q     E  financial  上市公司财务指标 - 息税折旧摊销前利润
========================================================================
['income_ebitda', 'ebitda']
```
从上面的返回值可以看出，在`qteasy`的内置历史数据类型中，EBITDA是一个标准的历史数据类型，可以通过'ebitda‘ / income_ebitda 这两个ID来获取（我们将使用'ebitda'），但是EV企业现金价值并不在内置数据类型中，但我们知道EV可以通过下面的公式计算：

$$ EV = 总市值 + 总负债 - 总现金 $$

而上面几个财务指标都是`qteasy`直接支持的：

- 总市值 - 数据类型： `total_mv`
- 总负债 - 数据类型： `total_liab`
- 总现金 - 数据类型： `c_cash_equ_end_period`

我们可以测试一下：

```python
htypes = 'total_mv, total_liab, c_cash_equ_end_period, ebitda'
# 获取沪深300指数成分股
shares = qt.filter_stock_codes(index='000300.SH', date='20220131')  
# 获取所有股票的总市值、总负债、总现金、EBITDA数据
dt = qt.get_history_data(htypes, shares=shares, asset_type='any', freq='m')
# 随便选择一支股票，转化为DataFrame检查数据是否正确获取
one_share = shares[24]
df = dt[one_share]
# 计算EV/EBITDA选股因子
df['ev_to_ebitda'] = (df.total_mv + df.total_liab - df.c_cash_equ_end_period) / df.ebitda

```
可以看到选股因子已经计算出来了，那么我们可以开始定义交易策略了。
## 用`FactorSorter`定义Alpha选股策略

针对这种定时选股类型的交易策略，`qteasy`提供了`FactorSorter`交易策略类，顾名思义，这个交易策略基类允许用户在策略的实现方法中计算一组选股因子，这样策略就可以自动将所有的股票按照选股因子的值排序，并选出排名靠前的股票。至于排序方法、筛选规则、股票持仓权重等都可以通过策略参数设置。

如果符合上面定义的交易策略，使用`FactorSorter`策略基类将会非常方便。

下面我们就来一步步定义看看，首先继承`FactorSorter`并定义一个类，在上一个章节中，我们在自定义策略的`__init__()`方法中定义名称、描述以及默认参数等信息，然而我们也可以忽略`__init__()`方法，仅仅在创建策略对象时传入参数等信息，这也是可以的，我们在这里就这样做：

```python
class AlphaFac(qt.FactorSorter):  # 注意这里使用FactorSorter策略类
    # 忽略__init__()方法，直接定义realize()方法
    def realize(self, h, **kwargs):
    	pass  
```

与上一节相同，在`realize()`中需要做的第一步是获取历史数据。我们知道历史数据包括`total_mv, total_liab, c_cash_equ_end_period, ebitda`等四种，这些历史数据同样是打包后存储在历史数据属性h中的。与上一章节不同的是，h是一个三维`ndarray`，形状（`shape`）为(L, M, N)，包含L层，M行、N列，分别代表每个股票、每个日期以及每种数据类型。

因此，要获取四种数据类型最后一个周期的所有股票的数据，应该使用如下方法切片：

```python
class AlphaFac(qt.FactorSorter):  # 注意这里使用FactorSorter策略类
    
    def realize(self, h, **kwargs):
        # 从历史数据编码中读取四种历史数据的最新数值
        total_mv = h[:, -1, 0]  # 总市值
        total_liab = h[:, -1, 1]  # 总负债
        cash_equ = h[:, -1, 2]  # 现金及现金等价物总额
        ebitda = h[:, -1, 3]  # ebitda，息税折旧摊销前利润
        ...
```
这样我们获取到的每一种数据类型都是一个一维数组，这个数组的长度与我们传入的备选股票池中的股票数量相同，每一个元素代表该股票的数据。加入我们的投资股票池中有三支股票，那么total_mv中就会有三个数字，分别代表三支股票的总市值，以此类推。

做好上述准备后，计算选股因子就非常方便了，而且，由于我们使用了`FactorSorter`策略基类，计算好选股因子后，直接返回选股因子就可以了，`qteasy`会处理剩下的选股操作：

```python
class AlphaFac(qt.FactorSorter):  # 注意这里使用FactorSorter策略类
    
    def realize(self, h, **kwargs):
        ... # 略
        # 选股因子为EV/EBIDTA，使用下面公式计算
        factor = (total_mv + total_liab - cash_equ) / ebitda
        return factor  # 直接返回选股因子，策略就定义完了
```

至此，仅仅用六行代码，一个自定义Alpha选股交易策略就定义好了。是不是非常简单？

好了，我们来看看回测的结果如何？

## 交易策略的回测结果

由于我们忽略了策略类的`__init__()`方法，因此在实例化策略对象时，必须输入完整的策略参数：
```python
alpha = AlphaFac(pars=(),
                 par_count=0,
                 par_types=[],
                 par_range=[],
                 name='AlphaSel',
                 description='本策略每隔1个月定时触发计算SHSE.000300成份股的过去的EV/EBITDA并选取EV/EBITDA大于0的股票',
                 data_types='total_mv, total_liab, c_cash_equ_end_period, ebitda',
                 strategy_run_freq='m',
                 data_freq='d',
                 window_length=100,
                 max_sel_count=30,  # 设置选股数量，最多选出30个股票
                 condition='greater',  # 设置筛选条件，仅筛选因子大于ubound的股票
                 ubound=0.0,  # 设置筛选条件，仅筛选因子大于0的股票
                 weighting='even',  # 设置股票权重，所有选中的股票平均分配权重
                 sort_ascending=True)  # 设置排序方式，因子从小到大排序选择头30名
```
然后创建一个`Operator`对象，因为我们希望控制持仓比例，因此最好使用“PT”信号类型：
```python
op = qt.Operator(alpha, signal_type='PT')
res = op.run(mode=1,
       asset_type='E',
       asset_pool=shares,
       PT_buy_threshold=0.0,
       PT_sell_threshold=0.0,
       trade_batch_size=100,
       sell_batch_size=1)
```
回测结果如下：

         ====================================
         |                                  |
         |       BACK TESTING RESULT        |
         |                                  |
         ====================================
    
    qteasy running mode: 1 - History back testing
    time consumption for operate signal creation: 9.4ms
    time consumption for operation back looping:  5s 831.0ms
    
    investment starts on      2016-04-05 00:00:00
    ends on                   2021-02-01 00:00:00
    Total looped periods:     4.8 years.
    
    -------------operation summary:------------
    Only non-empty shares are displayed, call 
    "loop_result["oper_count"]" for complete operation summary
    
              Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
    000301.SZ    1        2       3   10.3%      0.0%     89.7%  
    000786.SZ    2        3       5   27.5%      0.0%     72.5%  
    000895.SZ    1        0       1   62.6%      0.0%     37.4%  
    002001.SZ    2        2       4   55.8%      0.0%     44.2%  
    002007.SZ    3        1       4   68.3%      0.0%     31.7%  
    002027.SZ    2        9      11   41.3%      0.0%     58.7%  
    002032.SZ    2        0       2    5.9%      0.0%     94.1%  
    002044.SZ    1        1       2    1.8%      0.0%     98.2%  
    002049.SZ    1        1       2    5.1%      0.0%     94.9%  
    002050.SZ    4        5       9   13.8%      0.0%     86.2%  
    ...            ...     ...   ...      ...       ...       ...
    603517.SH    1        1       2    1.8%      0.0%     98.2%  
    603806.SH    6        3       9   39.8%      0.0%     60.2%  
    603899.SH    1        1       2   31.0%      0.0%     69.0%  
    000408.SZ    3        6       9   35.5%      0.0%     64.5%  
    002648.SZ    1        1       2    5.2%      0.0%     94.8%  
    002920.SZ    1        1       2    1.7%      0.0%     98.3%  
    300223.SZ    1        1       2    5.2%      0.0%     94.8%  
    600219.SH    1        1       2    6.1%      0.0%     93.9%  
    603185.SH    1        1       2    5.2%      0.0%     94.8%  
    688005.SH    1        1       2    5.2%      0.0%     94.8%   
    
    Total operation fee:     ¥      928.22
    total investment amount: ¥  100,000.00
    final value:              ¥  159,072.14
    Total return:                    59.07% 
    Avg Yearly return:               10.09%
    Skewness:                         -0.28
    Kurtosis:                          3.29
    Benchmark return:                65.96% 
    Benchmark Yearly return:         11.06%
    
    ------strategy loop_results indicators------ 
    alpha:                           -0.012
    Beta:                             1.310
    Sharp ratio:                      1.191
    Info ratio:                      -0.010
    250 day volatility:               0.105
    Max drawdown:                    20.49% 
        peak / valley:        2018-05-22 / 2019-01-03
        recovered on:         2019-12-26
    
    ===========END OF REPORT=============
    
![在这里插入图片描述](../examples/img/output_5_1_2.png)


回测结果显示这个策略并不能非常有效地跑赢沪深300指数，不过总体来说回撤较小一些，风险较低，是一个不错的保底策略。

但策略的表现并不是我们讨论的重点，下面我们再来看一看，如果不用`FactorSorter`基类，如何定义同样的Alpha选股策略。
## 用`GeneralStg`定义一个Alpha选股策略
前面已经提过了两种策略基类：

- **`RuleIterator`**： 用户只需要针对一支股票定义选股规则，`qteasy`便能将同样的规则应用到股票池中所有的恶股票上，而且还能针对不同股票设置不同的可调参数
- **`FactorSorter`**：用户只需要定义一个选股因子，`qteasy`便能根据选股因子自动排序后选择最优的股票持有，并卖掉不够格的股票。

而`GeneralStg`是`qteasy`提供的一个最基本的策略基类，它没有提供任何“语法糖”功能，帮助用户降低编码工作量，但是正是因为没有语法糖，它才是一个真正的“万能”策略类，可以用来更加自由地创建交易策略。

上面的Alpha选股交易策略可以很容易用`FactorSorter`实现，但为了了解`GeneralStg`，我们来看看如何使用它来创建相同的策略：

直接把完整的代码贴出来：

```python

class AlphaPT(qt.GeneralStg):
    
    def realize(self, h, r=None, t=None, pars=None):

        # 从历史数据编码中读取四种历史数据的最新数值
        total_mv = h[:, -1, 0]  # 总市值
        total_liab = h[:, -1, 1]  # 总负债
        cash_equ = h[:, -1, 2]  # 现金及现金等价物总额
        ebitda = h[:, -1, 3]  # ebitda，息税折旧摊销前利润
        
        # 选股因子为EV/EBIDTA，使用下面公式计算
        factors = (total_mv + total_liab - cash_equ) / ebitda
        # 处理交易信号，将所有小于0的因子变为NaN
        factors = np.where(factors < 0, np.nan, factors)
        # 选出数值最小的30个股票的序号
        arg_partitioned = factors.argpartition(30)
        selected = arg_partitioned[:30]  # 被选中的30个股票的序号
        not_selected = arg_partitioned[30:]  # 未被选中的其他股票的序号（包括因子为NaN的股票）
        
        # 开始生成PT交易信号
        signal = np.zeros_like(factors)
        # 所有被选中的股票的持仓目标被设置为0.03，表示持有3.3%
        signal[selected] = 0.0333
        # 其余未选中的所有股票持仓目标在PT信号模式下被设置为0，代表目标仓位为0
        signal[not_selected] = 0  
        
        return signal    
```
将上面的代码与`FactorSorter`的代码对比，可以发现，`GeneralStg`的代码在计算出选股因子以后，还多出了因子处理的工作：

- 剔除小于零的因子
- 排序并选出剩余因子中最小的30个
- 选出股票后将他们的持仓比例设置为3.3%

事实上，上面的这些工作都是`FactorSorter`提供的“语法糖”，在这里我们必须手动实现而已。值得注意的是，我在上面例子中使用的排序等代码都是从`FactorSorter`中直接提取出来的高度优化的`numpy`代码，它们的运行速度是很快的，比一般用户能写出的代码快很多，因此，只要条件允许，用户都应该尽量利用这些语法糖，只有在不得已的情况下才自己编写排序代码。

大家可以研究一下上面的代码，但是请注意，如果使用`GeneralStg`策略类，策略的输出应该是股票的目标仓位，而不是选股因子。

下面看看回测结果：

## 回测结果：

使用同样的数据进行回测：
```python
alpha = AlphaPT(pars=(),
                 par_count=0,
                 par_types=[],
                 par_range=[],
                 name='AlphaSel',
                 description='本策略每隔1个月定时触发计算SHSE.000300成份股的过去的EV/EBITDA并选取EV/EBITDA大于0的股票',
                 data_types='total_mv, total_liab, c_cash_equ_end_period, ebitda',
                 strategy_run_freq='m',
                 data_freq='d',
                 window_length=100)
op = qt.Operator(alpha, signal_type='PT')
res = op.run(mode=1,
             asset_type='E',
             asset_pool=shares,
             PT_buy_threshold=0.00,  # 如果设置PBT=0.00，PST=0.03，最终收益会达到30万元
             PT_sell_threshold=0.00,
             trade_batch_size=100,
             sell_batch_size=1,
             maximize_cash_usage=True,
             trade_log=True
            )
```
回测结果如下：
    
         ====================================
         |                                  |
         |       BACK TESTING RESULT        |
         |                                  |
         ====================================
    
    qteasy running mode: 1 - History back testing
    time consumption for operate signal creation: 7.2ms
    time consumption for operation back looping:  6s 308.5ms
    
    investment starts on      2016-04-05 00:00:00
    ends on                   2021-02-01 00:00:00
    Total looped periods:     4.8 years.
    
    -------------operation summary:------------
    Only non-empty shares are displayed, call 
    "loop_result["oper_count"]" for complete operation summary
    
              Sell Cnt Buy Cnt Total Long pct Short pct Empty pct
    000301.SZ    1        1       2   10.3%      0.0%     89.7%  
    000786.SZ    2        3       5   27.5%      0.0%     72.5%  
    000895.SZ    1        1       2   68.7%      0.0%     31.3%  
    002001.SZ    2        2       4   57.5%      0.0%     42.5%  
    002007.SZ    0        1       1   68.3%      0.0%     31.7%  
    002027.SZ    6        7      13   41.3%      0.0%     58.7%  
    002032.SZ    3        1       4    7.5%      0.0%     92.5%  
    002044.SZ    1        1       2    1.8%      0.0%     98.2%  
    002049.SZ    1        1       2    5.1%      0.0%     94.9%  
    002050.SZ    4        4       8   13.8%      0.0%     86.2%  
    ...            ...     ...   ...      ...       ...       ...
    603806.SH    5        3       8   62.1%      0.0%     37.9%  
    603899.SH    2        3       5   36.3%      0.0%     63.7%  
    000408.SZ    3        5       8   35.5%      0.0%     64.5%  
    002648.SZ    1        1       2    5.2%      0.0%     94.8%  
    002920.SZ    1        1       2    5.1%      0.0%     94.9%  
    300223.SZ    1        2       3    5.2%      0.0%     94.8%  
    300496.SZ    1        1       2   10.5%      0.0%     89.5%  
    600219.SH    1        1       2    6.1%      0.0%     93.9%  
    603185.SH    1        1       2    5.2%      0.0%     94.8%  
    688005.SH    1        2       3    5.2%      0.0%     94.8%   
    
    Total operation fee:     ¥      985.25
    total investment amount: ¥  100,000.00
    final value:              ¥  189,723.44
    Total return:                    89.72% 
    Avg Yearly return:               14.18%
    Skewness:                         -0.41
    Kurtosis:                          2.87
    Benchmark return:                65.96% 
    Benchmark Yearly return:         11.06%
    
    ------strategy loop_results indicators------ 
    alpha:                            0.044
    Beta:                             1.134
    Sharp ratio:                      1.284
    Info ratio:                       0.011
    250 day volatility:               0.120
    Max drawdown:                    20.95% 
        peak / valley:        2018-05-22 / 2019-01-03
        recovered on:         2019-09-09
    
    ===========END OF REPORT=============
    
![在这里插入图片描述](../examples/img/output_7_1.png)

两种交易策略的输出结果基本相同
## 本节回顾

通过本节的学习，我们了解了`qteasy`提供的另外两种交易策略基类`FactorSorter`和`GeneralStg`的使用方法，实际创建了两个交易策略，虽然使用不同的基类，但是创建出了基本相同的Alpha选股交易策略。

在下一个章节中，我们仍然将继续介绍自定义交易策略，但是会用一个更加复杂的例子来演示自定义交易策略的使用方法。敬请期待！
