
交易策略基类
================

在 qteasy 中，所有交易策略都基于 ``BaseStrategy`` 抽象基类：通过可调参数
（pars）、历史数据声明（data_types + window_length 等）以及 ``realize()`` 中
的交易逻辑生成不同风格的信号，最终由 Operator 按 PT/PS/VS 信号语义解析为具体
交易指令。更多关于 Strategy / Group / Operator 的架构与自定义策略教程，见设计
文档与 manage_strategies 系列文档。

.. autoclass:: qteasy.BaseStrategy

.. autofunction:: qteasy.BaseStrategy.__init__

.. autofunction:: qteasy.BaseStrategy.info

.. autofunction:: qteasy.BaseStrategy.update_par_values

.. autofunction:: qteasy.BaseStrategy.realize

.. autofunction:: qteasy.BaseStrategy.get_signal

.. autofunction:: qteasy.BaseStrategy.get_pars

三种交易策略类
=========================

GeneralStg
-------------------------

.. autoclass:: qteasy.GeneralStg

FactorSorter
------------

因子排序选股策略，根据用户定义的选股因子筛选排序后确定每个股票的选股权重(请注意，FactorSorter策略生成的交易信号在0到1之间，推荐设置signal_type为"PT")

这类策略要求用户从历史数据中提取一个选股因子，并根据选股因子的大小排序后确定投资组合中股票的交易信号
用户需要在realize()方法中计算选股因子，计算出选股因子后，接下来的排序和选股逻辑都不需要用户自行定义。
策略会根据预设的条件，从中筛选出符合标准的因子，并将剩下的因子排序，从中选择特定数量的股票，最后根据它
们的因子值分配权重或信号值。

这些选股因子的排序和筛选条件，由6个选股参数来控制，因此用户只需要在策略属性中设置好相应的参数，
策略就可以根据选股因子输出交易信号了。用户只需要集中精力思考选股因子的定义逻辑即可，无需费时费力编写
因子的筛选排序取舍逻辑了。

这六个选股参数如下：

    *max_sel_count:     float,  选股限额，表示最多选出的股票的数量，默认值：0.5，表示选中50%的股票
    *condition:         str ,   确定股票的筛选条件，默认值'any'
                                'any'        :默认值，选择所有可用股票
                                'greater'    :筛选出因子大于ubound的股票
                                'less'       :筛选出因子小于lbound的股票
                                'between'    :筛选出因子介于lbound与ubound之间的股票
                                'not_between':筛选出因子不在lbound与ubound之间的股票
    *lbound:            float,  执行条件筛选时的指标下界, 默认值np.-inf
    *ubound:            float,  执行条件筛选时的指标上界, 默认值np.inf
    *sort_ascending:    bool,   排序方法，默认值: False, True: 优先选择因子最小的股票, False, 优先选择因子最大的股票
    *weighting:         str ,   确定如何分配选中股票的权重
                                默认值: 'even'
                                'even'       :所有被选中的股票都获得同样的权重
                                'linear'     :权重根据因子排序线性分配
                                'distance'   :股票的权重与他们的指标与最低之间的差值（距离）成比例
                                'proportion' :权重与股票的因子分值成正比

realize()方法的输出：
FactorSorter交易策略的输出信号为1D ndarray，这个数组不是交易信号，而是选股因子，策略会根据选股因子
自动生成股票的交易信号，通常交易信号类型应该为PT，即使用选股因子控制股票的目标仓位。

    output：
            np.array(arr), 如： np.array[0.1, 1.0, 10.0, 100.0]

根据上述选股因子，FactorSorter()策略会根据其配置参数生成各个股票的目标仓位，
    例如：当
            max_sel_count=0.5
            condition='greater',
            ubound=0.5,
            weighting='even'
    时，上述因子的选股结果为:
            np.array[0.0, 0.0, 0.5, 0.5]

关于Strategy类的更详细说明，请参见qteasy的文档。

.. autoclass:: qteasy.FactorSorter

RuleIterator
--------------------------

规则迭代策略类。这一类策略不考虑每一只股票的区别，将同一套规则同时迭代应用到所有的股票上。

RuleIterator策略类的特殊功能是可以对同一套交易规则，将不同的参数应用到投资组合中的不同股票上。
例如，用户可以设计一个均线交叉策略，并将其应用到投资组合中的所有股票上，同时可以为每只股票
设定不同的均线周期参数。

例如，用户可以为投资组合中的股票分别设定不同的均线参数：
    stock1: short_window=5, long_window=20
    stock2: short_window=10, long_window=50
    stock3: short_window=20, long_window=100
    stock4: short_window=30, long_window=200

这样，用户只需要编写一套均线交叉的交易规则，就可以将其应用到投资组合中的所有股票上，同时
还可以为每只股票设定不同的均线参数。这种特殊的交易策略，需要用到RuleIterator类的
multi_pars属性。

这类策略要求用户针对投资组合中的一个投资品种设计交易规则，在realize()方法定义该交易规则，
策略可以把同样的交易规则应用推广到投资组合中的所有投资品种上，同时可以采用不同的策略参数。

realize()方法的输出：
realize()方法的输出就是交易信号，该交易信号是一个数字，策略会将其推广到整个投资组合：

    def realize(): -> int

    投资组合： [share1, share2, share3, share4]
                |        |       |       |
             [ int1,   int2,   int3,   int4 ] -> np.array[ int1,   int2,   int3,   int4]

按照前述规则设置好策略的参数，并在realize函数中定义好逻辑规则后，一个策略就可以被添加到Operator
中，并产生交易信号了。

关于Strategy类的更详细说明，请参见qteasy的文档。
RuleIterator 策略类继承了交易策略基类

.. autoclass:: qteasy.RuleIterator

交易策略的可调参数
-----------------------

Parameter对象包含Space对象的一个维度，Parameter对象有四种类型：

1，discr (int) Parameter，离散型数轴，包含一系列连续的整数，由这些整数值的上下界来定义。例如Parameter([0, 10])代表一个Parameter，这个Parameter上的
    取值范围为0～10，包括0与10
2，conti (float) Parameter，连续数轴对象，包含从下界到上界之间的所有浮点数，同样使用上下界定义，如Parameter([0., 2.0])
3，enum Parameter，枚举值数轴，取值范围为一系列任意类型对象，这些对象需要在创建Parameter的时候就定义好。
    例如：Parameter(['a', 1, 'abc', (1, 2, 3)])就是一个枚举轴，它的取值可以是以下列表中的任意一个
                    ['a', 1, 'abc', (1, 2, 3)]
4，array Parameter，数组数轴，取值范围为一个数组对象，这个数组对象可以是int/float类型的numpy array对象。

Parameter对象最重要的方法是gen_value()方法，代表从数轴的所有可能值中取出一部分并返回给Space对象生成迭代器。

对于Parameter对象来说，有两种基本的gen_value()方法：

    1，interval方法：间隔取值方法，即按照一定的间隔从数轴中取出一定数量的值。这种方法的参数主要是step_size，对于conti类型的数轴step_size可以为一个浮点数，对于其他类型的数轴，step_size只能为整数。取值的举例如下：
        a: 从一个conti数值轴中，以step_size=0.5取值：
            Parameter([0, 3]).gen_values(step_size=0.5) -> [0, 0.5, 1, 1.5, 2. 2.5, 3]
        b: 从一个discr数值轴中，以step_size=2取值:
            Parameter([1, 5]).gen_values(step_size-2) -> [1, 3, 5]
        c: 从一个enum轴中，以step_size=2取值:
            Parameter([1, 2, 3, 'a', 'b', 'c', (1, 2)]).gen_values(step_size=2) -> [1, 3, 'b', (1, 2)]
    2，random方法: 从数轴的所有可选值中随机选出指定数量的值返回到Space对象，对于任何类型的Parameter，其取值方法都是类似的，指定的取值数量必须是整数：举例如下：
        a: 从一个enum轴中随机取出四个值：
            Parameter(['a', 'b', 'c']).gen_values(count=4) -> ['b', 'a', 'c', 'a']

另外Parameter对象还有常规的set_value方法等

.. autoclass:: qteasy.Parameter

.. autofunction:: qteasy.Parameter.__init__

.. autofunction:: qteasy.Parameter.get_value

.. autofunction:: qteasy.Parameter.set_value

.. autofunction:: qteasy.Parameter.update_par_range
