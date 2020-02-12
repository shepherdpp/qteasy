# coding=utf-8
class Context():
    '''QT Easy量化交易系统的上下文对象，保存所有相关环境变量及(伪)常量

    包含的常量：
    ========
        RUN_MODE_LIVE = 0
        RUN_MODE_BACKLOOP = 1
        RUN_MODE_OPTIMIZE = 2

    包含的变量：
    ========
        mode，运行模式
    '''
    # 环境常量
    # ============
    RUN_MODE_LIVE = 0
    RUN_MODE_BACKLOOP = 1
    RUN_MODE_OPTIMIZE = 2

    OPTI_EXHAUSTIVE = 0
    OPTI_MONTECARLO = 1
    OPTI_INCREMENTAL = 2
    OPTI_GA = 3

    def __init__(self):
        '''初始化所有的环境变量和环境常量'''

        # 环境变量
        # ============
        self.mode = RUN_MODE_BACKLOOP
        self.rate_fee = rate_fee  # 交易费用成本计算参数，固定交易费率
        self.rate_slipery = rate_slipery  # 交易滑点成本估算参数，对交易命令发出到实际交易完成之间价格变化导致的成本进行估算
        self.rate_impact = rate_impact  # 交易冲击成本估算参数，对交易本身对价格造成的影响带来的成本进行估算
        self.MOQ = MOQ  # 交易最小批量，设置为0表示可以买卖分数股

        self.shares = []  # 优化参数所针对的投资产品
        self.opt_period_start = today - datetime.timedelta(3650)  # 优化历史区间开始日
        self.opt_period_end = today - datetime.timedelta(365)  # 优化历史区间结束日
        self.opt_period_freq = 'd'  # 优化历史区间采样频率
        self.loop_period_start = today - datetime.timedelta(3650)  # 测试区间开始日
        self.loop_period_end = today  # 测试区间结束日（测试区间的采样频率与优化区间相同）
        self.t_func_type = 1  # 'single'
        self.t_func = 'FV'  # 评价函数
        self.compound_method_expr = '( FV + Sharp )'  # 复合评价函数表达式，使用表达式解析模块解析并计算
        self.cycle_convolution_type = 'average'  # 当使用重叠区间优化参数时，各个区间评价函数值的组合方法
        self.opti_method = 'standard'

        pass