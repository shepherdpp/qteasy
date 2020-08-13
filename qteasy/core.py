# coding=utf-8
# core.py

import pandas as pd
import numpy as np
import numba as nb
import datetime
import itertools
import time
import math
import sys
from .history import get_history_panel, str_to_list
from concurrent.futures import ProcessPoolExecutor, as_completed

PROGRESS_BAR = {0 : '----------------------------------------', 1: '#---------------------------------------',
                2 : '##--------------------------------------', 3: '###-------------------------------------',
                4 : '####------------------------------------', 5: '#####-----------------------------------',
                6 : '######----------------------------------', 7: '#######---------------------------------',
                8 : '########--------------------------------', 9: '#########-------------------------------',
                10: '##########------------------------------', 11: '###########-----------------------------',
                12: '############----------------------------', 13: '#############---------------------------',
                14: '##############--------------------------', 15: '###############-------------------------',
                16: '################------------------------', 17: '#################-----------------------',
                18: '##################----------------------', 19: '###################---------------------',
                20: '####################--------------------', 21: '#####################-------------------',
                22: '######################------------------', 23: '#######################-----------------',
                24: '########################----------------', 25: '#########################---------------',
                26: '##########################--------------', 27: '###########################-------------',
                28: '############################------------', 29: '#############################-----------',
                30: '##############################----------', 31: '###############################---------',
                32: '################################--------', 33: '#################################-------',
                34: '##################################------', 35: '###################################-----',
                36: '####################################----', 37: '#####################################---',
                38: '######################################--', 39: '#######################################-',
                40: '########################################'
                }


class Log:
    """ 数据记录类，策略选股、择时、风险控制、交易信号生成、回测等过程中的记录的基类

    记录各个主要过程中的详细信息，并写入内存
    """

    def __init__(self):
        """

        """
        self.record = None
        raise NotImplementedError

    def write_record(self, *args):
        """

        :param args:
        :return:
        """

        raise NotImplementedError


# TODO: 将要增加PREDICT模式，完善predict模式所需的参数，完善其他优化算法的参数
# TODO: 完善Context类，将docstring中的所有参数和属性一一实现
class Context:
    """QT Easy量化交易系统的上下文对象，保存所有相关环境变量及参数

    所有系统执行相关的变量都存储在Context对象中，在调用core模块中的主要公有方法时，应该引用Context对象以提供所有的环境变量。

    包含的常量：
    ========
        RUN_MODE_LIVE = 0
        RUN_MODE_BACKLOOP = 1
        RUN_MODE_OPTIMIZE = 2
        RUN_MODE_PREDICT = 3

    包含的参数：
    ========
        基本参数：
            mode:                       int, 运行模式，包括实盘模式、回测模式和优化模式三种方式:
                                        {0: 实盘模式,
                                         1: 回测模式,
                                         2: 优化模式}

            mode_text,                  int, 只读属性，mode属性的解释文本
            share_pool:                 str, 投资资产池
            asset_type:                 str, 资产类型:
                                        {'E': 股票,
                                         'I': 指数,
                                         'F': 期货}
            asset_type_text:            str, 只读属性，asset_type属性的解释文本

            moq:                        float, 金融资产交易最小单位
            riskfree_interest_rate:     float, 无风险利率，在回测时可以选择考虑现金以无风险利率增长对资产价值和投资策略的影响
            parallel:                   bool, 是否启用多核CPU多进程模式加速优化，默认True，False表示只使用单核心
            print_log:                  bool, 默认False，是否将回测或优化记录中的详细信息打印在屏幕上

        实盘模式相关参数：
            account_name:               str,  账户用户名
            proxy_name:                 str,    代理服务器名
            server_name:                str,   服务器名
            password:                   str,      密码

        回测模式相关参数:
            reference_asset:            str, 用于对比回测收益率优劣的参照投资产品
            reference_asset_type:       str, 参照投资产品的资产类型: {'E': 股票, 'I': 指数, 'F': 期货}
            reference_data_type:        str, 参照投资产品的数据类型（'close', 'open' 等）
            rate:                       qteasy.Rate, 投资费率对象
            visual:                     bool, 默认False，可视化输出回测结果
            log:                        bool, 默认True，输出回测详情到log文件

        回测历史区间参数:
            invest_cash_amounts:        list, 只读属性，模拟回测的投资额分笔清单，通过cashplan对象获取
            invest_cash_dates:          list,  只读属性，模拟回测的投资额分笔投入时间清单，通过cashplan对象获取
            invest_start:               str, 投资开始日期
            invest_cash_type:           int, 投资金额类型，{0: 全部资金在投资起始日一次性投入, 1: 资金分笔投入（定投）}
            invest_cash_freq:           str, 资金投入频率，当资金分笔投入时有效
            invest_cash_periods:        str, 资金投入笔数，当资金分笔投入时有效
            invest_end:                 str, 完成资金投入的日期
            invest_total_amount:        float, 总投资额
            invest_unit_amount:         float, 资金单次投入数量，仅当资金分笔投入时有效
            riskfree_ir:                float, 无风险利率水平，在回测时可以选择是否计算现金的无风险增值或通货膨胀

            fixed_buy_fee:              float, 固定买入费用，买入资产时需要支付的固定费用
            fixed_sell_fee:             float, 固定卖出费用，卖出资产时需要支付的固定费用
            fixed_buy_rate:             float, 固定买入费率，买入资产时需要支付费用的费率
            fixed_sell_rate:            float, 固定卖出费率，卖出资产时需要支付费用的费率
            min_buy_fee:                float, 最小买入费用，买入资产时需要支付的最低费用
            min_sell_fee:               float, 最小卖出费用，卖出资产时需要支付的最低费用
            slippage:                   float, 滑点，通过不同的模型应用滑点率估算交易中除交易费用以外的成本，如交易滑点和冲击成本等
            rate_type:                  int, 费率计算模型，可以选用不同的模型以最佳地估算实际的交易成本
            visual:                     bool, 默认值True，是否输出完整的投资价值图表和详细报告
            performance_indicators:     str, 回测后对回测结果计算各种指标，支持的指标包括：格式为逗号分隔的字符串，如'FV, sharp'
                                        indicator           instructions
                                        FV                  终值
                                        sharp               夏普率
                                        alpha               阿尔法比率
                                        beta                贝塔比率
                                        information         信息比率

            loop_log_file_path:         str, 回测记录日志文件存储路径
            cash_inflate:               bool, 默认为False，现金增长，在回测时是否考虑现金的时间价值，如果为True，则现金按照无风险
                                        利率增长

        优化模式参数:
            opti_invest_amount:         float, 优化投资金额，优化时默认使用简单投资额，即一次性在优化期初投入所有金额
            opti_use_loop_cashplan:     bool, 是否使用回测的现金投资计划设置，默认False，如果使用复杂现金计划，会更加耗时
            opti_fixed_rate:            float, 优化回测交易费率，优化时默认使用简单投资费率，即固定费率，为了效率
            opti_use_loop_rate:         bool, 是否使用回测投资成本估算模型，默认False，如果使用复杂成本估算模型，会更加耗时

            opti_period_type:           int, 优化区间类型:
                                        {0: 单一优化区间，在一段历史数据区间上进行参数寻优,
                                         1: 多重优化区间，根据策略参数在几段不同的历史数据区间上的平均表现来确定最优参数}

            opti_start:                 str, 优化历史区间起点
            opti_window_span:           str, 优化历史区间跨度
            opti_window_count:          int, 当选择多重优化区间时，优化历史区间的数量
            opti_window_offset:         str, 当选择多重优化区间时，不同区间的开始间隔
            opti_weighting_type:        int 当选择多重优化区间时，计算平均表现分数的方法：
                                        {0: 简单平均值,
                                         1: 线性加权平均值,
                                         2: 指数加权平均值}

            test_period_type:           int, 参数测试区间类型，在一段历史数据区间上找到最优参数后，可以在同一个区间上测试最优参数的
                                        表现，也可以在不同的历史数据区间上测试（这是更好的办法），选项有三个：
                                        {0: 相同区间,
                                         1: 接续区间,
                                         2: 自定义区间}

            test_period_offset:         str, 如果选择自定义区间，测试区间与寻优区间之间的间隔
            test_window_span:           str, 测试历史区间跨度
            target_function:            str, 作为优化目标的评价函数
            larger_is_better:           bool, 确定目标函数的优化方向，保留函数值最大的还是最小的结果，默认True，寻找函数值最大的结果

            opti_method:                int, 不同的优化参数搜索算法：
                                        {0: Exhaustive，固定步长搜索法,
                                         1: MonteCarlo，蒙特卡洛搜索法 ,
                                         2: Incremental，递减步长搜索 ,
                                         3: GA，遗传算法 ,
                                         4: ANN，基于机器学习或神经网络的算法}

            opti_method_step_size:      [int, tuple], 用于固定步长搜索法，固定搜索步长
            opti_method_sample_size:    int, 用于蒙特卡洛搜索法，在空间中随机选取的样本数量
            opti_method_init_step_size: int, 用于递减步长搜索法，初始步长
            opti_method_incre_ratio:    float, 用于递减步长搜索法，步长递减比率
            opti_method_screen_size:    int, 用于递减步长搜索法，每一轮搜索保留的结果数量
            opti_method_min_step_size:  int, 用于递减步长搜索法，最小搜索步长
            opti_method_population:     int, 用于遗传算法，种群数量
            opti_method_swap_rate:      float, 用于遗传算法，交换比率
            opti_methdo_crossover_rate: float, 用于遗传算法，交配比率
            opti_method_mute_rate:      float, 用于遗传算法，变异比率
            opti_method_max_generation: int, 用于遗传算法，最大传递代数

            opti_output_count:          int, 输出结果的个数
            opti_log_file_path:         str, 输出结果日志文件的保存路径
            opti_perf_report:           bool, 是否对所有结果进行详细表现评价，默认False，True时会生成所有策略在测试历史区间的详细评价报告
            opti_report_indicators:     str, 用于上述详细评价报告的评价指标，格式为逗号分隔的字符串，如'FV, sharp, information'

        预测模式参数:
            predict:                    bool, 默认False，决定是否利用蒙特卡洛方法对未来的策略表现进行统计预测
            pred_period:                str, 如果对策略的未来表现进行预测，这是预测期
            pred_cycles:                int, 蒙特卡洛预测的预测次数
            pred_report_indicators:     str, 预测分析的报告中所涉及的评价指标，格式为逗号分隔的字符串，如'FV, sharp, information'

    """
    # TODO: 完善context对象的信息属性
    run_mode_text = {0: 'Real-time Running Mode',
                     1: 'Back-looping Mode',
                     2: 'Optimization Mode',
                     3: 'Predict Mode'}

    asset_type_text = {'E': 'equity',
                       'I': 'index',
                       'F': 'futures'}

    test_period_type_text = {0: '', 1: '', 2: '', 3: ''}

    opti_mode_text = {0: 'Exhaustive searching method, searches the parameter space over all posible vectors '
                         'at a fixed step size',
                      1: 'MonteCarlo searching method, searches randomly distributed vectors in the parameter space',
                      2: 'Decremental step size, searches the parameter space in multiple rounds, each time with '
                         'decreasing step size to provide increased accuracy over rounds',
                      3: 'Genetic Algorithm, searches for local optimal parameter by adopting genetic evolution laws'}

    def __init__(self,
                 mode: int = 1,
                 moq: float = 0.,
                 riskfree_interest_rate: float = 0.035,
                 visual: bool = False):
        """初始化所有的环境变量和环境常量

        input:
            :param mode: 操作模式：{0: 实盘操作模式, 1: 历史数据回测模式, 2: 历史数据优化模式}
            :param moq: 最小交易单位
            :param riskfree_interest_rate: 无风险利率水平
            :param visual: 是否输出可视化结果

        更多参数含义见Context类的docstring
        """
        today = datetime.datetime.today().date()

        self.mode = mode
        self.share_pool = None
        self.asset_type = 'E'

        self.moq = moq
        self.riskfree_interest_rate = riskfree_interest_rate
        self.parallel = True
        self.print_log = False

        self.account_name = None
        self.proxy_name = None
        self.server_name = None
        self.password = None

        self.reference_asset = None
        self.reference_asset_type = 'E'
        self.reference_data_type = 'close'
        self.rate = Cost()
        self.visual = visual
        self.log = True

        # TODO: 这里除了invest_dates 以及invest_amounts以外，其他的参数均不起作用，需要重新规划
        self.invest_start = (today - datetime.timedelta(3650)).strftime('%Y%m%d')
        self.invest_cash_type = 0
        self.invest_cash_freq = 'Y'
        self.invest_cash_periods = 5
        self.invest_end = today.strftime('%Y%m%d')
        self.invest_total_amount = 50000
        self.invest_unit_amount = 10000
        self.riskfree_ir = 0.015
        self.invest_dates = '20060801'
        self.invest_amounts = [10000]
        self.cash_plan = CashPlan(self.invest_dates, self.invest_amounts)

        self.fixed_buy_fee = 5
        self.fixed_sell_fee = 0
        self.fixed_buy_rate = 0.0035
        self.fixed_sell_rate = 0.0015
        self.min_buy_fee = 5
        self.min_sell_fee = 5
        self.slippage = 0.01
        self.rate_type = 0
        self.visual = True
        self.performance_indicators = 'FV'

        self.loop_log_file_path = None
        self.cash_inflate = False

        self.opti_invest_amount = 10000
        self.opti_use_loop_cashplan = False
        self.opti_fixed_rate = 0.0035
        self.opti_use_loop_rate = False

        self.opti_period_type = 0

        self.opti_start = (today - datetime.timedelta(3650)).strftime('%Y%m%d')
        self.opti_window_span = '3Y'
        self.opti_window_count = 5
        self.opti_window_offset = '1Y'
        self.opti_weighting_type = 0

        self.test_period_type = 0

        self.test_period_offset = 180
        self.test_window_span = '1Y'
        self.target_function = 'FV'
        self.larger_is_better = True

        self.opti_method = 0

        self.opti_method_step_size = 1
        self.opti_method_sample_size = 1000
        self.opti_method_init_step_size = 16
        self.opti_method_incre_ratio = 2
        self.opti_method_screen_size = 100
        self.opti_method_min_step_size = 1
        self.opti_method_population = 1000
        self.opti_method_swap_rate = 0.3
        self.opti_methdo_crossover_rate = 0.2
        self.opti_method_mute_rate = 0.2
        self.opti_method_max_generation = 10000

        self.opti_output_count = 64
        self.opti_log_file_path = ''
        self.opti_perf_report = False
        self.opti_report_indicators = 'FV, Sharp'

    def __str__(self):
        """定义Context类的打印样式"""
        out_str = list()
        out_str.append(f'{type(self)} at {hex(id(self))}')
        out_str.append('qteasy running information:')
        out_str.append('===========================')
        out_str.append(f'execution mode:          {self.mode} - {self.mode_text}\n'
                       f'')
        return ''.join(out_str)

    @property
    def mode_text(self):
        return self.run_mode_text[self.mode]

    @property
    def asset_type_text(self):
        return self.asset_type_text[self.asset_type]

    @property
    def invest_cash_amounts(self):
        return None

    @property
    def invest_cash_dates(self):
        return None


# TODO: 对Rate对象进行改进，实现以下功能：1，最低费率，2，卖出和买入费率不同，3，固定费用，4，与交易量相关的二阶费率
# TODO: 将Rate类改为Cost类
class Cost:
    """ 交易成本类，用于在回测过程中对交易成本进行估算

    交易成本的估算依赖三种类型的成本：
    1， fix：type：float，固定费用，在交易过程中产生的固定现金费用，与交易金额和交易量无关： 固定费用 = 固定费用
    2， fee：type：float，交易费率，或者叫一阶费率，交易过程中的固定费率，交易费用 = 交易金额 * 交易费率
    3， slipage：type：float，交易滑点，或者叫二阶费率。
        用于模拟交易过程中由于交易延迟或买卖冲击形成的交易成本，滑点绿表现为一个关于交易量的函数, 交易
        滑点成本等于该滑点率乘以交易金额： 滑点成本 = f(交易金额） * 交易成本
    """

    def __init__(self,
                 buy_fix: float = 0.0,
                 sell_fix: float = 0.0,
                 buy_rate: float = 0.003,
                 sell_rate: float = 0.001,
                 buy_min: float = 5.0,
                 sell_min: float = 0.0,
                 slipage: float = 0.0):
        self.buy_fix = buy_fix
        self.sell_fix = sell_fix
        self.buy_rate = buy_rate
        self.sell_rate = sell_rate
        self.buy_min = buy_min
        self.sell_min = sell_min
        self.slipage = slipage

    def __str__(self):
        """设置Rate对象的打印形式"""
        return f'<Buying: {self.buy_fix}, rate:{self.buy_rate}, slipage:{self.slipage}\n' \
               f'Selling: {self.sell_fix}, rate:{self.sell_rate}>'

    def __repr__(self):
        """设置Rate对象"""
        return f'Rate({self.fix}, {self.fee}, {self.slipage})'

    # TODO: Rate对象的调用结果应该返回交易费用而不是交易费率，否则固定费率就没有意义了(交易固定费用在回测中计算较为复杂)
    def __call__(self,
                 trade_values: np.ndarray,
                 is_buying: bool = True,
                 fixed_fees: bool = False) -> np.ndarray:
        """直接调用对象，计算交易费率或交易费用

        采用两种模式计算：
            当fixed_fees为True时，采用固定费用模式计算，返回值为包含滑点的交易成本列表，
            当fixed_fees为False时，采用固定费率模式计算，返回值为包含滑点的交易成本率列表

        :param trade_values: ndarray: 总交易金额清单
        :param is_buying: bool: 当前是否计算买入费用或费率
        :param fixed_fees: bool: 当前是否采用固定费用模式计算
        :return:
        np.ndarray,
        """
        if fixed_fees:  # 采用固定费用模式计算
            if is_buying:
                return self.buy_fix + self.slipage * trade_values ** 2
            else:
                return self.sell_fix + self.slipage * trade_values ** 2
        else:  # 采用固定费率模式计算
            if is_buying:
                if self.buy_min == 0:
                    return self.buy_rate + self.slipage * trade_values
                else:
                    min_rate = self.buy_min / (trade_values - self.buy_min)
                    return np.fmax(self.buy_rate, min_rate) + self.slipage * trade_values
            else:
                if self.sell_min == 0:
                    return self.sell_rate + self.slipage * trade_values
                else:
                    min_rate = self.sell_min / trade_values
                    return np.fmax(self.sell_rate, min_rate) + self.slipage * trade_values

    def __getitem__(self, item: str) -> float:
        """通过字符串获取Rate对象的某个组份（费率、滑点或冲击率）"""
        assert isinstance(item, str), 'TypeError, item should be a string in ' \
                                      '[\'buy_fix\', \'sell_fix\', \'buy_rate\', \'sell_rate\',' \
                                      ' \'buy_min\', \'sell_min\',\'slipage\']'
        if item == 'buy_fix':
            return self.buy_fix
        elif item == 'sell_fix':
            return self.sell_fix
        elif item == 'buy_rate':
            return self.buy_rate
        elif item == 'sell_rate':
            return self.sell_rate
        elif item == 'buy_min':
            return self.buy_min
        elif item == 'sell_min':
            return self.sell_min
        elif item == 'slipage':
            return self.slipage
        else:
            raise TypeError

    def get_selling_result(self, prices: np.ndarray, op: np.ndarray, amounts: np.ndarray):
        """计算出售投资产品的要素


        :param prices: 投资产品的价格
        :param op: 交易信号
        :param amounts: 持有投资产品的份额

        :return:
        a_sold:
        fee:
        cash_gained: float
        fee: float
        """
        a_sold = np.where(prices, np.where(op < 0, amounts * op, 0), 0)
        sold_values = a_sold * prices
        if self.sell_fix == 0:  # 固定交易费用为0，按照交易费率模式计算
            rates = self.__call__(trade_values=amounts * prices, is_buying=False, fixed_fees=False)
            # debug
            # print(f'selling rate is {rates}')
            cash_gained = (-1 * sold_values * (1 - rates)).sum()
            fee = (sold_values * rates).sum()
        else:
            fixed_fees = self.__call__(trade_values=amounts * prices, is_buying=False, fixed_fees=True)
            fee = -np.where(a_sold, fixed_fees, 0).sum()
            cash_gained = - sold_values.sum() + fee
        return a_sold, cash_gained, fee

    def get_purchase_result(self, prices: np.ndarray, op: np.ndarray, pur_values: [np.ndarray, float], moq: float):
        """获得购买资产时的要素

        :param prices: ndarray, 投资组合中每只股票的当前单价
        :param op: ndarray, 操作矩阵，针对投资组合中的每只股票的买卖操作，>0代表买入或平空仓,<0代表卖出或平多仓，绝对值表示买卖比例
        :param pur_values: ndarray, 买入金额，可用于买入股票或资产的计划金额
        :param moq: float, 最小交易单位
        :return:
        a_purchased: 一个ndarray, 代表所有股票分别买入的份额或数量
        cash_spent: float，花费的总金额，包括费用在内
        fee: 花费的费用，购买成本，包括佣金和滑点等投资成本
        """
        if self.buy_fix == 0:
            # 固定费用为0，按照费率模式计算
            rates = self.__call__(trade_values=pur_values, is_buying=True, fixed_fees=False)
            # debug
            # print(f'purchase rate is {rates}')
            # 费率模式下，计算综合费率（包含滑点）
            if moq == 0:  # moq为0，买入份额数为任意分数份额
                a_purchased = np.where(prices,
                                       np.where(op > 0,
                                                pur_values / (prices * (1 + rates)),
                                                0),
                                       0)
            else:  # moq不为零，买入份额必须是moq的倍数
                a_purchased = np.where(prices,
                                       np.where(op > 0,
                                                pur_values // (prices * moq * (1 + rates)) * moq,
                                                0),
                                       0)
            cash_spent = np.where(a_purchased, -1 * a_purchased * prices * (1 + rates), 0)
            fee = -(cash_spent * rates / (1 + rates)).sum()
        elif self.buy_fix:
            # 固定费用不为0，按照固定费用模式计算费用，忽略费率并且忽略最小费用，只计算买入金额大于固定费用的份额
            fixed_fees = self.__call__(trade_values=pur_values, is_buying=True, fixed_fees=True)
            if moq == 0:
                a_purchased = np.fmax(np.where(prices,
                                               np.where(op > 0,
                                                        (pur_values - fixed_fees) / prices,
                                                        0),
                                               0),
                                      0)
            else:
                a_purchased = np.fmax(np.where(prices,
                                               np.where(op > 0,
                                                        (pur_values - fixed_fees) // (prices * moq) * moq,
                                                        0),
                                               0),
                                      0)
            cash_spent = np.where(a_purchased, -1 * a_purchased * prices - fixed_fees, 0)
            fee = np.where(a_purchased, fixed_fees, 0).sum()
        return a_purchased, cash_spent.sum(), fee


# TODO: 在qteasy中所使用的所有时间日期格式统一使用pd.TimeStamp格式
class CashPlan:
    """ 现金计划类，在策略回测的过程中用来模拟固定日期的现金投资额

    投资计划对象包含一组带时间戳的投资金额数据，用于模拟在固定时间的现金投入，可以实现对一次性现金投入和资金定投的模拟
    """

    def __init__(self, dates: [list, str], amounts: [list, str, int, float], interest_rate: float = 0.0):
        """

        :param dates:
        :param amounts:
        :param interest_rate: float
        """
        from collections import Iterable
        if isinstance(amounts, (int, float)):
            amounts = [amounts]
        assert isinstance(amounts,
                          (list, np.ndarray)), f'TypeError: amounts should be Iterable, got {type(amounts)} instead'
        if isinstance(amounts, list):
            for amount in amounts:  # 检查是否每一个amount的数据类型
                assert isinstance(amount, (int, float, np.int64, np.float64)), \
                    f'TypeError: amount should be number format, got {type(amount)} instead'
                assert amount > 0, f'InputError: Investment amount should be larger than 0'
        assert isinstance(dates, Iterable), f"Expect Iterable input dates, got {type(dates)} instead!"

        if isinstance(dates, str):
            dates = dates.replace(' ', '')
            dates = dates.split(',')
        try:
            dates = list(map(pd.to_datetime, dates))
        except:
            raise KeyError(f'some of the input strings can not be converted to date time format!')

        assert len(amounts) == len(dates), \
            f'InputError: number of amounts should be equal to that of dates, can\'t match {len(amounts)} amounts in' \
            f' to {len(dates)} days.'

        self._cash_plan = pd.DataFrame(amounts, index=dates, columns=['amount']).sort_index()
        assert isinstance(interest_rate, float), \
            f'TypeError, interest rate should be a float number, got {type(interest_rate)}'
        assert 0. <= interest_rate <= 1., \
            f'InputError, interest rate should be between 0 and 100%, got {interest_rate:.2%}'
        self._ir = interest_rate

    @property
    def first_day(self):
        """ 返回投资第一天的日期

        :return: pd.Timestamp
        """
        return self.dates[0]

    @property
    def last_day(self):
        """ 返回投资期最后一天的日期

        :return: pd.Timestamp
        """
        return self.dates[-1]

    @property
    def period(self):
        """ 返回第一次投资到最后一次投资之间的时长，单位为天

        :return: int
        """
        return (self.last_day - self.first_day).days

    @property
    def investment_count(self):
        """ 返回在整个投资计划期间的投资次数

        :return: int
        """
        return len(self.dates)

    @property
    def dates(self):
        """ 返回整个投资计划期间的所有投资日期，按从先到后排列

        :return: list[pandas.Timestamp]
        """
        return list(self.plan.index)

    @property
    def amounts(self):
        """ 返回整个投资计划期间的所有投资额列表，按从先到后排列

        :return: list[float]
        """
        return list(self.plan.amount)

    @property
    def total(self):
        """ 返回整个投资计划期间的投资额总和，不考虑利率

        :return: float
        """
        return self.plan.amount.sum()

    @property
    def ir(self):
        """ 无风险利率，年化利率

        :return: float
        """
        return self._ir

    @ir.setter
    def ir(self, ir: float):
        """ 设置无风险利率

        :param ir: float, 无风险利率
        :return:
        """
        assert isinstance(ir, float), f'The interest rate should be a float number, not {type(ir)}'
        assert 0. < ir < 1., f'Interest rate should be between 0 and 1'
        self._ir = ir

    @property
    def closing_value(self):
        """ 计算所有投资额按照无风险利率到最后一个投资额的终值

        :return: float
        """
        if self.ir == 0:
            return self.total
        else:
            df = self.plan.copy()
            df['days'] = (df.index[-1] - df.index).days
            df['fv'] = df.amount * (1 + self.ir) ** (df.days / 365.)
            return df.fv.sum()

    @property
    def opening_value(self):
        """ 计算所有投资额按照无风险利率在第一个投资日的现值

        :return: float
        """
        if self.ir == 0:
            return self.total
        else:
            df = self.plan.copy()
            df['days'] = (df.index - df.index[0]).days
            df['pv'] = df.amount / (1 + self.ir) ** (df.days / 365.)
            return df.pv.sum()

    @property
    def plan(self):
        """ 返回整个投资区间的投资计划，形式为DataFrame

        :return: pandas.DataFrame
        """
        return self._cash_plan

    def to_dict(self, keys: [list, np.ndarray] = None):
        """ 返回整个投资区间的投资计划，形式为字典。默认key为日期，如果明确给出keys，则使用参数keys

        :return: dict
        """
        if keys is None:
            return dict(self.plan.amount)
        else:
            # assert isinstance(keys, list), f'TypeError, keys should be list, got {type(keys)} instead.'
            assert len(keys) == len(self.amounts), \
                f'InputError, count of elements in keys should be same as that of investment amounts, expect ' \
                f'{len(self.amounts)}, got {len(keys)}'
            return dict(zip(keys, self.amounts))

    def info(self):
        """ 打印投资计划的所有信息

        :return: None
        """
        import sys
        print(f'\n{type(self)}')
        if self.investment_count > 1:
            print('Investment contains multiple entries')
            print(f'Investment Period from {self.first_day.date()} to {self.last_day.date()}, '
                  f'lasting {self.period} days')
            print(f'Total investment count: {self.investment_count} entries, total invested amount: ¥{self.total:,.2f}')
            print(f'Interest rate: {self.ir:.2%}, equivalent final value: ¥{self.closing_value:,.2f}:')
        else:
            print(f'Investment is one-off amount of ¥{self.total:,.2f} on {self.first_day.date()}')
            print(f'Interest rate: {self.ir:.2%}, equivalent final value: ¥{self.closing_value:,.2f}:')
        print(self.plan)
        print(f'memory usage: {sys.getsizeof(self.plan)} bytes\n')

    def __add__(self, other):
        """ 两个CashPlan对象相加，得到一个新的CashPlan对象，这个对象包含两个CashPlan对象的投资计划的并集，如果两个投资计划的时间
            相同，则新的CashPlan的投资计划每个投资日的投资额是两个投资计划的和

            CashPlan对象与一个int或float对象相加，得到的新的CashPlan对象的每笔投资都增加int或float数额

        :param other: (int, float, CashPlan): 另一个对象，根据对象类型不同行为不同
        :return:
        """

        if isinstance(other, (int, float)):
            # 当other是一个数字时，在新的CashPlan的每个投资日期的投资额上加上other元
            min_amount = np.min(self.amounts)
            assert other > -min_amount, \
                f'ValueError, the amount will cause illegal invest value in plan, {min_amount} - {other}'
            new_amounts = np.array(self.amounts) + other
            return CashPlan(self.dates, new_amounts, self.ir)
        elif isinstance(other, CashPlan):
            plan1 = self._cash_plan
            plan2 = other._cash_plan
            index_combo = list(plan1.index)
            index_combo.extend(list(plan2.index))
            index_combo = list(set(index_combo))  # 新的CashPlan的投资日期集合是两个CashPlan的并集
            plan1 = plan1.reindex(index_combo).fillna(0)  # 填充Nan值避免相加后产生Nan值
            plan2 = plan2.reindex(index_combo).fillna(0)
            plan = (plan1 + plan2).sort_index()
            if self.ir == 0:
                new_ir = other.ir
            else:
                new_ir = self.ir
            return CashPlan(list(plan.index), list(plan.amount), new_ir)
        else:
            raise TypeError(f'Only CashPlan and int objects are supported, got {type(other)}')

    def __radd__(self, other):
        """ 另一个对象other + CashPlan的结果与CashPlan + other相同， 即：
            other + CashPlan == CashPlan + other

        :param other:
        :return:
        """
        return self.__add__(other)

    def __mul__(self, other):
        """CashPlan乘以一个int或float返回一个新的CashPlan，它的投资数量和投资日期与CashPlan对象相同，每次投资额增加int或float倍

        :param other: (int, float):
        :return:
        """
        assert isinstance(other, (int, float))
        assert other >= 0
        new_dates = list(self.dates)
        new_amounts = list(np.array(self.amounts) * other)
        return CashPlan(new_dates, new_amounts, self.ir)

    def __rmul__(self, other):
        """ other 乘以一个CashPlan的结果是一个新的CashPlan，结果取决于other的类型：
            other 为 int时，新的CashPlan的投资次数重复int次，投资额不变，投资日期按照相同的频率顺延，如果CashPlan只有一个投资日期时
                频率为一年
            other 为 float时，other * CashPlan == CashPlan * other

        :param other:
        :return:
        """
        assert isinstance(other, (int, float))
        if isinstance(other, int):
            assert other > 1
            one_day = pd.Timedelta(1, 'd')
            one_month = pd.Timedelta(31, 'd')
            one_quarter = pd.Timedelta(93, 'd')
            one_year = pd.Timedelta(365, 'd')
            if self.investment_count == 1:  # 如果只有一次投资，则以一年为间隔
                new_dates = [self.first_day + one_year * i for i in range(other)]
                return CashPlan(new_dates, self.amounts * other, self.ir)
            else:  # 如果有两次或以上投资，则计算首末两次投资之间的间隔，以此为依据计算未来投资间隔
                if self.investment_count == 2:  # 当只有两次投资时，新增投资的间距与频率与两次投资的间隔相同
                    time_offset = pd.Timedelta(self.period * 2, 'd')
                else:  # 当投资次数多于两次时，整个投资作为一个单元，未来新增投资为重复每个单元的投资。单元的跨度可以为月、季度及年
                    if self.period <= 28:
                        time_offset = one_month
                    elif self.period <= 90:
                        time_offset = one_quarter
                    elif self.period <= 365:
                        time_offset = one_year
                    else:
                        time_offset = one_year * (self.period // 365 + 1)
                # 获取投资间隔后，循环生成所有的投资日期
                original_dates = self.dates
                new_dates = self.dates
                for i in range(other - 1):
                    for date in original_dates:
                        new_dates.append(date + time_offset * (i + 1) + one_day)
                return CashPlan(new_dates, self.amounts * other, self.ir)

        else:  # 当other是浮点数时，返回CashPlan * other 的结果
            return self.__mul__(other)

    def __repr__(self):
        """

        :return:
        """
        return self.__str__()

    def __str__(self):
        """ 打印cash plan

        :return:
        """
        return self._cash_plan.__str__()

    def __getitem__(self, item):
        """

        :param item:
        :return:
        """
        return self.plan[item]


# TODO: 实现多种方式的定投计划，可定制周期、频率、总金额、单次金额等简单功能，同时还应支持递增累进式定投、按照公式定投等高级功能
def distribute_investment(amount: float,
                          start: str,
                          end: str,
                          periods: int,
                          freq: str) -> CashPlan:
    """ 将投资额拆分成一系列定投金额，并生成一个CashPlan对象

    :param amount:
    :param start:
    :param end:
    :param periods:
    :param freq:
    :return:
    """


def _loop_step(pre_cash: float,
               pre_amounts: np.ndarray,
               op: np.ndarray,
               prices: np.ndarray,
               rate: Cost,
               moq: float,
               print_log: bool = False) -> tuple:
    """ 对单次交易进行处理，采用向量化计算以提升效率

    input：=====
        param pre_cash, np.ndarray：本次交易开始前账户现金余额
        param pre_amounts, np.ndarray：list，交易开始前各个股票账户中的股份余额
        param op, np.ndarray：本次交易的个股交易清单
        param prices：np.ndarray，本次交易发生时各个股票的价格
        param rate：object Rate 交易成本率对象
        param moq：float: 投资产品最小交易单位，moq为0时允许交易任意数额的金融产品，moq不为零时允许交易的产品数量是moq的整数倍

    return：===== tuple，包含四个元素
        cash：交易后账户现金余额
        amounts：交易后每个个股账户中的股份余额
        fee：本次交易总费用
        value：本次交易后资产总额（按照交易后现金及股份余额以及交易时的价格计算）
    """
    # 计算交易前现金及股票余额在当前价格下的资产总额
    pre_value = pre_cash + (pre_amounts * prices).sum()
    if print_log:
        print(f'本期开始, 期初现金: {pre_cash:.2f}, 期初总资产: {pre_value:.2f}')
        print(f'本期交易信号{op}')
    # 计算按照交易清单出售资产后的资产余额以及获得的现金
    # 根据出售持有资产的份额数量计算获取的现金
    a_sold, cash_gained, fee_selling = rate.get_selling_result(prices=prices,
                                                               op=op,
                                                               amounts=pre_amounts)
    if print_log:
        print(f'以本期资产价格{prices}出售资产 {-a_sold}')
        print(f'获得现金:{cash_gained:.2f}, 产生交易费用 {fee_selling:.2f}')
    # 本期出售资产后现金余额 = 期初现金余额 + 出售资产获得现金总额
    cash = pre_cash + cash_gained
    # 初步估算按照交易清单买入资产所需要的现金，如果超过持有现金，则按比例降低买入金额
    pur_values = pre_value * op.clip(0)  # 使用clip来代替np.where，速度更快,且op.clip(1)比np.clip(op, 0, 1)快很多
    if print_log:
        print(f'本期计划买入资产动用资金: {pur_values.sum():.2f}')
    if pur_values.sum() > cash:
        # 估算买入资产所需现金超过持有现金
        pur_values = pur_values / pre_value * cash
        if print_log:
            print(f'由于持有现金不足，调整动用资金数量为: {pur_values.sum():.2f}')
            # 按比例降低分配给每个拟买入资产的现金额度
    # 计算购入每项资产实际花费的现金以及实际买入资产数量，如果MOQ不为0，则需要取整并修改实际花费现金额
    a_purchased, cash_spent, fee_buying = rate.get_purchase_result(prices=prices,
                                                                   op=op,
                                                                   pur_values=pur_values,
                                                                   moq=moq)
    if print_log:
        print(f'以本期资产价格{prices}买入资产 {a_purchased}')
        print(f'实际花费现金 {cash_spent:.2f} 并产生交易费用: {fee_buying:.2f}')
    # 计算购入资产产生的交易成本，买入资产和卖出资产的交易成本率可以不同，且每次交易动态计算
    fee = fee_buying + fee_selling
    # 持有资产总额 = 期初资产余额 + 本期买入资产总额 + 本期卖出资产总额（负值）
    amounts = pre_amounts + a_purchased + a_sold
    # 期末现金余额 = 本期出售资产后余额 + 本期购入资产花费现金总额（负值）
    cash += cash_spent.sum()
    # 期末资产总价值 = 期末资产总额 * 本期资产单价 + 期末现金余额
    value = (amounts * prices).sum() + cash
    if print_log:
        print(f'期末现金: {cash:.2f}, 期末总资产: {value:.2f}\n')
    return cash, amounts, fee, value


def _get_complete_hist(looped_value: pd.DataFrame,
                       h_list: pd.DataFrame,
                       with_price: bool = False) -> pd.DataFrame:
    """完成历史交易回测后，填充完整的历史资产总价值清单

    input:=====
        :param values：完成历史交易回测后生成的历史资产总价值清单，只有在操作日才有记录，非操作日没有记录
        :param h_list：完整的投资产品价格清单，包含所有投资产品在回测区间内每个交易日的价格
        :param with_price：Bool，True时在返回的清单中包含历史价格，否则仅返回资产总价值
    return: =====
        values，pandas.DataFrame：重新填充的完整历史交易日资产总价值清单
    """
    # 获取价格清单中的投资产品列表
    # print(f'looped values raw data info: {looped_value.info()}')
    shares = h_list.columns  # 获取资产清单
    start_date = looped_value.index[0]  # 开始日期
    looped_history = h_list.loc[start_date:]  # 回测历史数据区间 = [开始日期:]
    # print(f'looped history info: \n{looped_history.info()}')
    # 使用价格清单的索引值对资产总价值清单进行重新索引，重新索引时向前填充每日持仓额、现金额，使得新的
    # 价值清单中新增的记录中的持仓额和现金额与最近的一个操作日保持一致，并消除nan值
    purchased_shares = looped_value[shares].reindex(looped_history.index, method='ffill').fillna(0)
    cashes = looped_value['cash'].reindex(looped_history.index, method='ffill').fillna(0)
    fees = looped_value['fee'].reindex(looped_history.index).fillna(0)
    looped_value = looped_value.reindex(looped_history.index)
    looped_value[shares] = purchased_shares
    looped_value.fee = fees
    looped_value.cash = cashes
    # print(f'extended looped value according to looped history: \n{looped_value.info()}')
    # 重新计算整个清单中的资产总价值，生成pandas.Series对象
    looped_value['value'] = (looped_history * looped_value[shares]).sum(axis=1) + looped_value['cash']
    if with_price:  # 如果需要同时返回价格，则生成pandas.DataFrame对象，包含所有历史价格
        share_price_column_names = []
        for name in shares:
            share_price_column_names.append(name + '_p')
        looped_value[share_price_column_names] = looped_history[shares]
    return looped_value


# TODO: 回测主入口函数需要增加回测结果可视化和回测结果参照标准
# TODO: 增加一个参数，允许用户选择是否考虑现金的无风险利率增长
# TODO: 并将过程和信息输出到log文件或log信息中，返回log信息
def apply_loop(op_list: pd.DataFrame,
               history_list: pd.DataFrame,
               visual: bool = False,
               price_visual: bool = False,
               cash_plan: CashPlan = None,
               cost_rate: Cost = None,
               moq: float = 100.,
               inflation_rate: float = 0.03,
               print_log: bool = False) -> pd.DataFrame:
    """使用Numpy快速迭代器完成整个交易清单在历史数据表上的模拟交易，并输出每次交易后持仓、
        现金额及费用，输出的结果可选

    input：=====
        :param cash_plan: float: 初始资金额，未来将被替换为CashPlan对象
        :param price_visual: Bool: 选择是否在图表输出时同时输出相关资产价格变化，visual为False时无效，未来将增加reference数据
        :param history_list: object pd.DataFrame: 完整历史价格清单，数据的频率由freq参数决定
        :param visual: Bool: 可选参数，默认False，仅在有交易行为的时间点上计算持仓、现金及费用，
                            为True时将数据填充到整个历史区间，并用图表输出
        :param op_list: object pd.DataFrame: 标准格式交易清单，描述一段时间内的交易详情，每次交易一行数据
        :param cost_rate: float Rate: 交易成本率对象，包含交易费、滑点及冲击成本
        :param moq: float：每次交易的最小份额单位
        :param inflation_rate: float, 现金的时间价值率，如果>0，则现金的价值随时间增长，增长率为inflation_rate

    output：=====
        Value_history: pandas.DataFrame: 包含交易结果及资产总额的历史清单

    """
    assert not op_list.empty, 'InputError: The Operation list should not be Empty'
    assert cost_rate is not None, 'TypeError: cost_rate should not be None type'
    assert cash_plan is not None, 'ValueError: cash plan should not be None type'

    # 根据最新的研究实验，在python3.6的环境下，nditer的速度显著地慢于普通的for-loop
    # 因此改回for-loop执行，知道找到更好的向量化执行方法
    # 提取交易清单中的所有数据，生成np.ndarray，即所有的交易信号
    op = op_list.values
    # 从价格清单中提取出与交易清单的日期相对应日期的所有数据
    price = history_list.fillna(0).loc[op_list.index].values

    looped_dates = list(op_list.index)
    # 如果inflation_rate > 0 则还需要计算所有有交易信号的日期相对前一个交易信号日的现金增长比率，这个比率与两个交易信号日之间的时间差有关
    if inflation_rate > 0:
        # print(f'looped dates are like: {looped_dates}')
        days_timedelta = looped_dates - np.roll(looped_dates, 1)
        # print(f'days differences between two operations dates are {days_timedelta}')
        days_difference = np.zeros_like(looped_dates, dtype='int')
        for i in range(1, len(looped_dates)):
            days_difference[i] = days_timedelta[i].days
        inflation_factors = 1 + days_difference * inflation_rate / 250
        # debug
        # print(f'number of difference in days are {days_difference}, inflation factors are {inflation_factors}')
    op_count = op.shape[0]  # 获取行数
    # 获取每一个资金投入日在历史时间序列中的位置
    investment_date_pos = np.searchsorted(looped_dates, cash_plan.dates)
    invest_dict = cash_plan.to_dict(investment_date_pos)
    # debug
    # print(f'investment date position calculated: {investment_date_pos}')
    # 初始化计算结果列表
    cash = 0  # 持有现金总额，期初现金总额总是0，在回测过程中到现金投入日时再加入现金
    amounts = [0] * len(history_list.columns)  # 投资组合中各个资产的持有数量，初始值为全0向量
    cashes = []  # 中间变量用于记录各个资产买入卖出时消耗或获得的现金
    fees = []  # 交易费用，记录每个操作时点产生的交易费用
    values = []  # 资产总价值，记录每个操作时点的资产和现金价值总和
    amounts_matrix = []
    date_print_format = '%Y/%m/%d'
    for i in range(op_count):  # 对每一行历史交易信号开始回测
        if print_log:
            print(f'交易日期:{looped_dates[i].strftime(date_print_format)}')
        if inflation_rate > 0:  # 现金的价值随时间增长，需要依次乘以inflation 因子，且只有持有现金增值，新增的现金不增值
            cash *= inflation_factors[i]
            if print_log:
                print(f'考虑现金增值, 上期现金: {(cash / inflation_factors[i]):.2f}, 经过{days_difference[i]}天后'
                      f'现金增值到{cash:.2f}')
        if i in investment_date_pos:
            # 如果在交易当天有资金投入，则将投入的资金加入可用资金池中
            cash += invest_dict[i]
            if print_log:
                print(f'本期新增投入现金, 本期现金: {(cash - invest_dict[i]):.2f}, 追加投资后现金增加到{cash:.2f}')
        # 调用loop_step()函数，计算下一期剩余资金、资产组合的持有份额、交易成本和下期资产总额
        # debug
        # print('before:', cash, amounts, op[i], price[i], cost_rate, moq)
        cash, amounts, fee, value = _loop_step(pre_cash=cash,
                                               pre_amounts=amounts,
                                               op=op[i], prices=price[i],
                                               rate=cost_rate,
                                               moq=moq,
                                               print_log=print_log)
        # 保存计算结果
        # debug
        # print('after:', cash, amounts, fee)
        cashes.append(cash)
        fees.append(fee)
        values.append(value)
        amounts_matrix.append(amounts)
    # 将向量化计算结果转化回DataFrame格式
    value_history = pd.DataFrame(amounts_matrix, index=op_list.index,
                                 columns=op_list.columns)

    # 填充标量计算结果
    value_history['cash'] = cashes
    value_history['fee'] = fees
    value_history['value'] = values
    # debug
    # print(value_history)
    if visual:  # Visual参数为True时填充完整历史记录并
        complete_value = _get_complete_hist(looped_value=value_history,
                                            h_list=history_list,
                                            with_price=price_visual)
        # 输出相关资产价格
        if price_visual:  # 当Price_Visual参数为True时同时显示所有的成分股票的历史价格
            shares = history_list.columns
            complete_value.plot(grid=True, figsize=(15, 7), legend=True,
                                secondary_y=shares)
        else:  # 否则，仅显示总资产的历史变化情况
            complete_value.plot(grid=True, figsize=(15, 7), legend=True)
        return complete_value
    return value_history


def get_current_holdings() -> tuple:
    """ 获取当前持有的产品在手数量

    :return: tuple:
    """
    return NotImplementedError


# TODO: add predict mode 增加predict模式，使用蒙特卡洛方法预测股价未来的走势，并评价策略在各种预测走势中的表现，进行策略表现的统计评分
def run(operator, context):
    """开始运行，qteasy模块的主要入口函数

        接受context上下文对象和operator执行器对象作为主要的运行组件，根据输入的运行模式确定运行的方式和结果
        根据context中的设置和运行模式（mode）进行不同的操作：
        context.mode == 0 or mode == 0:
            进入实时信号生成模式：
            根据context实时策略运行所需的历史数据，根据历史数据实时生成操作信号
            策略参数不能为空
        context.mode == 1 or mode == 1:
            进入回测模式：
            根据context规定的回测区间，使用History模块联机读取或从本地读取覆盖整个回测区间的历史数据
            生成投资资金模型，模拟在回测区间内使用投资资金模型进行模拟交易的结果
            输出对结果的评价（使用多维度的评价方法）
            输出回测日志·
            投资资金模型不能为空，策略参数不能为空
        context.mode == 2 or mode == 2:
            进入优化模式：
            根据context规定的优化区间和回测区间，使用History模块联机读取或本地读取覆盖整个区间的历史数据
            生成待优化策略的参数空间，并生成投资资金模型
            使用指定的优化方法在优化区间内查找投资资金模型的全局最优或局部最优参数组合集合
            使用在优化区间内搜索到的全局最优策略参数在回测区间上进行多次回测并再次记录结果
            输出最优参数集合在优化区间和回测区间上的评价结果
            输出优化及回测日志
            投资资金模型不能为空，策略参数可以为空
        context.mode == 3 or mode == 3:
            进入评价模式（技术冻结后暂停开发此功能）
            评价模式的思想是使用随机生成的模拟历史数据对策略进行评价。由于可以使用大量随机历史数据序列进行评价，因此可以得到策略的统计学
            表现
    input：

        :param operator: Operator()，策略执行器对象
        :param context: Context()，策略执行环境的上下文对象
    return：=====
        type: Log()，运行日志记录，txt 或 pd.DataFrame
    """
    import time
    # 从context 上下文对象中读取运行所需的参数：
    # 股票清单或投资产品清单
    # shares = context.share_pool
    reference_data = context.reference_asset
    # 如果没有显式给出运行模式，则按照context上下文对象中的运行模式运行，否则，适用mode参数中的模式
    run_mode = context.mode
    run_mode_text = context.mode_text

    # 根据根据operation对象和context对象的参数生成不同的历史数据用于不同的用途：
    # 用于交易信号生成的历史数据
    # TODO: 生成的历史数据还应该基于更多的参数，比如采样频率、以及提前期等
    op_start = (pd.to_datetime(context.invest_start) + pd.Timedelta(value=-420, unit='d')).strftime('%Y%m%d')
    # debug
    print(f'preparing historical data, \ninvestment start date: {op_start}, '
          f'\noperation generation dependency start date: {op_start}\n'
          f'end date: {context.invest_end}\nshares: {context.share_pool}\n'
          f'htypes: {operator.op_data_types} at frequency \'{operator.op_data_freq}\'')
    hist_op = get_history_panel(start=op_start,
                                end=context.invest_end,
                                shares=context.share_pool,
                                htypes=operator.op_data_types,
                                freq=operator.op_data_freq,
                                asset_type=context.asset_type,
                                chanel='online')
    hist_loop = hist_op.to_dataframe(htype='close')  # 用于数据回测的历史数据
    # TODO: 应该根据需要生成用于优化的历史数据
    hist_opti = None  # 用于策略优化的历史数据
    # 生成参考历史数据，作为参考用于回测结果的评价
    # debug
    # print(f'preparing reference historical data, \n '
    #       f'\noperation generation dependency start date: {context.invest_start}\n'
    #       f'end date: {context.invest_end}\nshares: {context.reference_asset}\n'
    #       f'htypes: {context.reference_data_type} at frequency \'{operator.op_data_freq}\'')
    hist_reference = (get_history_panel(start=context.invest_start,
                                        end=context.invest_end,
                                        shares=context.reference_asset,
                                        htypes=context.reference_data_type,
                                        freq=operator.op_data_freq,
                                        asset_type=context.reference_asset_type,
                                        chanel='online')).to_dataframe(htype='close')
    # debug
    print(f'reference hist data downloaded, info: \n{hist_reference.info()}\n'
          f'operation hist data downloaded, info: \n{hist_op.info()}')
    # ===============
    # 开始正式的策略运行，根据不同的运行模式，运行的程序不同
    # ===============~~
    print(f'====================================\n'
          f'       RUNNING IN MODE {run_mode}\n'
          f'      --{run_mode_text}--\n'
          f'====================================\n')
    if run_mode == 0:
        """进入实时信号生成模式：
        
            根据生成的执行器历史数据hist_op，应用operator对象中定义的投资策略生成当前的投资组合和各投资产品的头寸及仓位
            连接交易执行模块登陆交易平台，获取当前账号的交易平台上的实际持仓组合和持仓仓位
            将生成的投资组合和持有仓位与实际仓位比较，生成交易信号
            交易信号为一个tuple，包含以下组分信息：
             1，交易品种：str，需要交易的目标投资产品，可能为股票、基金、期货或其他，根据建立或设置的投资组合产品池确定
             2，交易位置：int，分别为多头头寸：1，或空头仓位： -1 （空头头寸只有在期货或期权交易时才会涉及到）
             3，交易方向：int，分别为开仓：1， 平仓：0 （股票和基金的交易只能开多头（买入）和平多头（卖出），基金可以开、平空头）
             4，交易类型：int，分为市价单：0，限价单：0
             5，交易价格：float，仅当交易类型为限价单时有效，市价单
             6，交易量：float，当交易方向为开仓（买入）时，交易量代表计划现金投入量，当交易方向为平仓（卖出）时，交易量代表卖出的产品份额
             
             上述交易信号被传入交易执行模块，连接券商服务器执行交易命令，执行成功后返回1，否则返回0
             若交易执行模块交易成功，返回实际成交的品种、位置、方向、价格及成交数量（交易量），另外还返回交易后的实际持仓数额，资金余额
             交易费用等信息
             
             以上信息被记录到log对象中，并最终存储在磁盘上
        """
        operator.prepare_data(hist_data=hist_op, cash_plan=context.cash_plan)  # 在生成交易信号之前准备历史数据
        st = time.time()  # 记录交易信号生成耗时
        op_list = operator.create_signal(hist_data=hist_op)  # 生成交易清单
        et = time.time()
        run_time_prepare_data = (et - st)
        if context:
            # 根据context对象的某个属性确定后续的步骤：要么从磁盘上读取当前持仓，要么手动输入当前持仓，要么假定当前持仓为0
            pass
        else:
            pass
        amounts = [0] * len(context.share_pool)
        print(f'==================================== \n'
              f'        OPERATION SIGNALS\n'
              f'====================================')
        print(f'\ntime consumption for operate signal creation: {time_str_format(run_time_prepare_data)}\n')
        print(f'Operation signals are generated on {op_list.index[0]}\nends on {op_list.index[-1]}\n'
              f'Total signals generated: {len(op_list.index)}.')
        print(f'Operation signal for shares on {op_list.index[-1].date()}')
        for share, signal in op_list.iloc[-1].iteritems():
            print(f'share {share}:')
            if signal > 0:
                print(f'Buy in with {signal * 100}% of total investment value!')
            elif signal < 0:
                print(f'Sell out {-signal * 100}% of current on holding stock!')
        print(f'\n===========END OF REPORT=============\n')
    elif run_mode == 1:
        """进入回测模式：
        
            根据执行器历史数据hist_op，应用operator执行器对象中定义的投资策略生成一张投资产品头寸及仓位建议表。
            这张表的每一行内的数据代表在这个历史时点上，投资策略建议对每一个投资产品应该持有的仓位。每一个历史时点的数据都是根据这个历史时点的
            相对历史数据计算出来的。这张投资仓位建议表的历史区间受context上下文对象的"loop_period_start, loop_period_end, loop_period_freq"
            等参数确定。
            同时，这张投资仓位建议表是由operator执行器对象在hist_op策略生成历史数据上生成的。hist_op历史数据包含所有用于生成策略运行结果的信息
            包括足够的数据密度、足够的前置历史区间以及足够的历史数据类型（如不同价格种类、不同财报指标种类等）
            operator执行器对象接受输入的hist_op数据后，在数据集合上反复循环运行，从历史数据中逐一提取出一个个历史片段，根据这个片段生成一个投资组合
            建议，然后把所有生成的投资组合建议组合起来形成完整的投资组合建议表。
            
            投资组合建议表生成后，系统在整个投资组合建议区间上比较前后两个历史时点上的建议持仓份额，当发生建议持仓份额变动时，根据投资产品的类型
            生成投资交易信号，包括交易方向、交易产品和交易量。形成历史交易信号表。
            
            历史交易信号表生成后，系统在相应的历史区间中创建hist_loop回测历史数据表，回测历史数据表包含对回测操作来说必要的历史数据如股价等，然后
            在hist_loop的历史数据区间上对每一个投资交易信号进行模拟交易，并且逐个生成每个交易品种的实际成交量、成交价格、交易费用（通过Rate类估算）
            以及交易前后的持有资产数量和持有现金数量的变化，以及总资产的变化。形成一张交易结果清单。交易模拟过程中的现金投入过程通过CashPlan对象来
            模拟。
            
            因为交易结果清单是根据有交易信号的历史交易日上计算的，因此并不完整。根据完整的历史数据，系统可以将数据补充完整并得到整个历史区间的
            每日甚至更高频率的投资持仓及总资产变化表。完成这张表后，系统将在这张总资产变化表上执行完整的回测结果分析，分析的内容包括：
                1，total_investment                      总投资
                2，total_final_value                     投资期末总资产
                3，loop_length                           投资模拟区间长度
                4，total_earning                         总盈亏
                5，total_transaction_cost                总交易成本
                6，total_open                            总开仓次数
                7，total_close                           总平仓次数
                8，total_return_rate                     总收益率
                9，annual_return_rate                    总年化收益率
                10，reference_return                     基准产品总收益
                11，reference_return_rate                基准产品总收益率
                12，reference_annual_return_rate         基准产品年化收益率
                13，max_retreat                          投资期最大回测率
                14，Karma_rate                           卡玛比率
                15，Sharp_rate                           夏普率
                16，win_rage                             胜率
                
            上述所有评价结果和历史区间数据能够以可视化的方式输出到图表中。同时回测的结果数据和回测区间的每一次模拟交易记录也可以被记录到log对象中
            保存在磁盘上供未来调用
            
        """
        operator.prepare_data(hist_data=hist_op, cash_plan=context.cash_plan)  # 在生成交易信号之前准备历史数据
        st = time.time()  # 记录交易信号生成耗时
        op_list = operator.create_signal(hist_data=hist_op)  # 生成交易清单
        # print(f'created operation list is: \n{op_list}')
        et = time.time()
        run_time_prepare_data = (et - st)
        st = time.time()  # 记录交易信号回测耗时
        looped_values = apply_loop(op_list=op_list,
                                   history_list=hist_loop.fillna(0),
                                   cash_plan=context.cash_plan,
                                   moq=context.moq,
                                   visual=context.visual,
                                   cost_rate=context.rate,
                                   price_visual=context.visual,
                                   print_log=context.print_log)
        et = time.time()
        run_time_loop_full = (et - st)
        # print('looped values result is: \n', looped_values)
        # 对回测的结果进行基本评价（回测年数，操作次数、总投资额、总交易费用（成本）
        years, oper_count, total_invest, total_fee = _eval_operation(op_list=op_list,
                                                                     looped_value=looped_values,
                                                                     cash_plan=context.cash_plan)
        # 评价回测结果——计算回测终值
        final_value = _eval_fv(looped_val=looped_values)
        # 评价回测结果——计算总投资收益率
        ret = final_value / total_invest
        # 评价回测结果——计算最大回撤比例以及最大回撤发生日期
        max_drawdown, low_date = _eval_max_drawdown(looped_values)
        # 评价回测结果——计算投资期间的波动率系数
        volatility = _eval_volatility(looped_values)
        # 评价回测结果——计算参考数据收益率以及平均年化收益率
        ref_rtn, ref_annual_rtn = _eval_benchmark(looped_values, hist_reference, reference_data)
        # 评价回测结果——计算投资期间的beta贝塔系数
        beta = _eval_beta(looped_values, hist_reference, reference_data)
        # 评价回测结果——计算投资期间的夏普率
        sharp = _eval_sharp(looped_values, total_invest, 0.035)
        # 评价回测结果——计算投资期间的alpha阿尔法系数
        alpha = _eval_alpha(looped_values, total_invest, hist_reference, reference_data)
        # 格式化输出回测结果
        # TODO: 将回测的更详细结果及回测的每一次操作详情登记到log文件中（可选内容）
        print(f'==================================== \n'
              f'           LOOPING RESULT\n'
              f'====================================')
        print(f'\nqteasy running mode: 1 - History back looping\n'
              f'time consumption for operate signal creation: {time_str_format(run_time_prepare_data)} ms\n'
              f'time consumption for operation back looping: {time_str_format(run_time_loop_full)} ms\n')
        print(f'investment starts on {looped_values.index[0]}\nends on {looped_values.index[-1]}\n'
              f'Total looped periods: {years} years.')
        print(f'operation summary:\n {oper_count}\nTotal operation fee:     ¥{total_fee:11,.2f}')
        print(f'total investment amount: ¥{total_invest:11,.2f}\n'
              f'final value:             ¥{final_value:11,.2f}')
        print(f'Total return: {ret * 100:.3f}% \nAverage Yearly return rate: {(ret ** (1 / years) - 1) * 100: .3f}%')
        print(f'Total reference return: {ref_rtn * 100:.3f}% \n'
              f'Average Yearly reference return rate: {ref_annual_rtn * 100:.3f}%')
        print(f'strategy performance indicators: \n'
              f'alpha:               {alpha:.3f}\n'
              f'Beta:                {beta:.3f}\n'
              f'Sharp rate:          {sharp:.3f}\n'
              f'250 day volatility:  {volatility:.3f}\n'
              f'Max drawdown:        {max_drawdown * 100:.3f}% on {low_date}')
        print(f'\n===========END OF REPORT=============\n')
    elif run_mode == 2:
        """进入策略优化模式：
        
            优化模式的目的是寻找能让策略的运行效果最佳的参数或参数组合。
            寻找能使策略的运行效果最佳的参数组合并不是一件容易的事，因为我们通常认为运行效果最佳的策略是能在"未来"实现最大收益的策略。但是，鉴于
            实际上要去预测未来是不可能的，因此我们能采取的优化方法几乎都是以历史数据——也就是过去的经验——为基础的，并且期望通过过去的历史经验
            达到某种程度上"预测未来"的效果。
            
            策略优化模式或策略优化器的工作方法就基于这个思想，如果某个或某组参数使得某个策略的在过去足够长或者足够有代表性的历史区间内表现良好，
            那么很有可能它也能在有限的未来不大会表现太差。因此策略优化模式的着眼点完全在于历史数据——所有的操作都是通过解读历史数据，或者策略在历史数据
            上的表现来评判一个策略的优劣的，至于如何找到对策略的未来表现有更大联系的历史数据或表现形式，则是策略设计者的责任。策略优化器仅仅
            确保找出的参数组合在过去有很好的表现，而对于未来无能为力。
            
            优化器的工作基础在于历史数据。它的工作方法从根本上来讲，是通过检验不同的参数在同一组历史区间上的表现来评判参数的优劣的。优化器的
            工作方法可以大体上分为以下两类：
            
                1，无监督方法类：这一类方法不需要事先知道"最优"或先验信息，从未知开始搜寻最佳参数。这类方法需要大量生成不同的参数组合，并且
                在同一个历史区间上反复回测，通过比较回测的结果而找到最优或较优的参数。这一类优化方法的假设是，如果这一组参数在过去取得了良好的
                投资结果，那么很可能在未来也不会太差。
                这一类方法包括：
                    1，Exhaustive_searching                  穷举法：
                    2，Montecarlo_searching                  蒙特卡洛法
                    3，Incremental_steped_searching          步进搜索法
                    4，Genetic_Algorithm                     遗传算法
                
                2，有监督方法类：这一类方法依赖于历史数据上的（有用的）先验信息：比如过去一个区间上的已知交易信号、或者价格变化信息。然后通过
                优化方法寻找历史数据和有用的先验信息之间的联系（目标联系）。这一类优化方法的假设是，如果这些通过历史数据直接获取先验信息的联系在未来仍然
                有效，那么我们就可能在未来同样根据这些联系，利用已知的数据推断出对我们有用的信息。
                这一类方法包括：
                    1，ANN_based_methods                     基于人工神经网络的有监督方法
                    2，SVM                                   支持向量机类方法
                    3，KNN                                   基于KNN的方法
                    
            为了实现上面的方法，优化器需要两组历史数据，分别对应两个不同的历史区间，一个是优化区间，另一个是回测区间。在优化的第一阶段，优化器
            在优化区间上生成交易信号，或建立目标联系，并且在优化区间上找到一个或若干个表现最优的参数组合或目标联系，接下来，在优化的第二阶段，
            优化器在回测区间上对寻找到的最优参数组合或目标联系进行测试，在回测区间生成对所有中选参数的“独立”表现评价。通常，可以选择优化区间较
            长且较早，而回测区间较晚而较短，这样可以模拟根据过去的信息建立的策略在未来的表现。
            
            优化器的优化过程首先开始于一个明确定义的参数"空间"。参数空间在系统中定义为一个Space对象。如果把策略的参数用向量表示，空间就是所有可能
            的参数组合形成的向量空间。对于无监督类方法来说，参数空间容纳的向量就是交易信号本身或参数本身。而对于有监督算法，参数空间是将历史数据
            映射到先验数据的一个特定映射函数的参数空间，例如，在ANN方法中，参数空间就是神经网络所有神经元连接权值的可能取值空间。优化器的工作本质
            就是在这个参数空间中寻找全局最优解或局部最优解。因此理论上所有的数值优化方法都可以用于优化器。
            
            优化器的另一个重要方面是目标函数。根据目标函数，我们可以对优化参数空间中的每一个点计算出一个目标函数值，并根据这个函数值的大小来评判
            参数的优劣。因此，目标函数的输出应该是一个实数。对于无监督方法，目标函数与参数策略的回测结果息息相关，最直接的目标函数就是投资终值，
            当初始投资额相同的时候，我们可以简单地认为终值越高，则参数的表现越好。但目标函数可不仅仅是终值一项，年化收益率或收益率、夏普率等等
            常见的评价指标都可以用来做目标函数，甚至目标函数可以用复合指标，如综合考虑收益率、交易成本、最大回撤等指标的一个复合指标，只要目标函数
            的输出是一个实数，就能被用作目标函数。而对于有监督方法，目标函数表征的是从历史数据到先验信息的映射能力，通常用实际输出与先验信息之间
            的差值的函数来表示。在机器学习和数值优化领域，有多种函数可选，例如MSE函数，CrossEntropy等等。
        """
        how = context.opti_method
        operator.prepare_data(hist_data=hist_op, cash_plan=context.cash_plan)  # 在生成交易信号之前准备历史数据
        pars, perfs = 0, 0
        if how == 0:
            """ Exhausetive Search 穷举法
            
                穷举法是最简单和直接的参数优化方法，在已经定义好的参数空间中，按照一定的间隔均匀地从向量空间中取出一系列的点，逐个在优化空间
                中生成交易信号并进行回测，把所有的参数组合都测试完毕后，根据目标函数的值选择排名靠前的参数组合即可。
                
                穷举法能确保找到参数空间中的全剧最优参数，不过必须逐一测试所有可能的参数点，因此计算量相当大。同时，穷举法只适用于非连续的参数
                空间，对于连续空间，仍然可以使用穷举法，但无法真正"穷尽"所有的参数组合
                
                关于穷举法的具体参数和输出，参见self._search_exhaustive()函数的docstring
            """
            pars, perfs = _search_exhaustive(hist=hist_op,
                                             op=operator,
                                             context=context,
                                             step_size=context.opti_method_step_size,
                                             parallel=context.parallel)
        elif how == 1:
            """ Montecarlo蒙特卡洛方法
            
                蒙特卡洛法与穷举法类似，也需要检查并测试参数空间中的大量参数组合。不过在蒙特卡洛法中，参数组合是从参数空间中随机选出的，而且在
                参数空间中均匀分布。与穷举法相比，蒙特卡洛方法更适合于连续参数空间。
                
                关于蒙特卡洛方法的参数和输出，参见self._search_montecarlo()函数的docstring
            """
            pars, perfs = _search_montecarlo(hist=hist_op,
                                             op=operator,
                                             context=context,
                                             point_count=context.opti_method_sample_size,
                                             parallel=context.parallel)
        elif how == 2:
            """ Incremental Stepped Search 递进步长法
            
                递进步长法本质上与穷举法是一样的。不过规避了穷举法的计算量过大的缺点，大大降低了计算量，同时在对最优结果的搜索能力上并未作出太大
                牺牲。递进步长法的基本思想是对参数空间进行多轮递进式的搜索，第一次搜索时使用一个相对较大的搜索步长，由于搜索的步长较大（通常为8或
                16，或者更大）因此第一次搜索的计算量只有标准穷举法的1/16^3或更少。第一次搜索完毕后，选出结果最优的参数点，通常为50个到1000个之
                间，在这些参数点的"附件"进行第二轮搜索，此时搜索的步长只有第一次的1/2或1/3。虽然搜索步长减小，但是搜索的空间更小，因此计算量也
                不大。第二轮搜索完成后，继续减小搜索步长，同样对上一轮搜索中找到的最佳参数附近搜索。这样循环直到完成整个空间的搜索。
                
                使用这种技术，在一个250*250X250的空间中，能够把搜索量从15,000,000降低到28,000左右,缩减到原来的1/500。如果目标函数在参数空间
                中大体上是连续的情况下，使用ISS方法可以以五百分之一的计算量得到近似穷举法的搜索效果。
                
                关于递进步长法的参数和输出，参见self._search_incremental()函数的docstring
            """
            pars, perfs = _search_incremental(hist=hist_op,
                                              op=operator,
                                              context=context,
                                              init_step=context.opti_method_init_step_size,
                                              min_step=context.opti_method_min_step_size,
                                              inc_step=context.opti_method_incre_ratio,
                                              parallel=context.parallel)
        elif how == 3:
            """ GA method遗传算法
            
                遗传算法适用于"超大"参数空间的参数寻优。对于有二到三个参数的策略来说，使用蒙特卡洛或穷举法是可以承受的选择，如果参数数量增加到4到
                5个，递进步长法可以帮助降低计算量，然而如果参数有数百个，而且每一个都有无限取值范围的时候，任何一种基于穷举的方法都没有应用的
                意义了。如果目标函数在参数空间中是连续且可微的，可以使用基于梯度的方法，但如果目标函数不可微分，GA方法提供了一个在可以承受的时间
                内找到全局最优或局部最优的方法。
                
                GA方法受生物进化论的启发，通过模拟生物在自然选择下的基因进化过程，在复杂的超大参数空间中搜索全局最优或局部最优参数。GA的基本做法
                是模拟一个足够大的"生物"种群在自然环境中的演化，这些生物的"基因"是参数空间中的一个点，在演化过程中，种群中的每一个个体会发生
                变异、也会通过杂交来改变或保留自己的"基因"，并把变异或杂交后的基因传递到下一代。在每一代的种群中，优化器会计算每一个个体的目标函数
                并根据目标函数的大小确定每一个个体的生存几率和生殖几率。由于表现较差的基因生存和生殖几率较低，因此经过数万乃至数十万带的迭代后，
                种群中的优秀基因会保留并演化出更加优秀的基因，最终可能演化出全局最优或至少局部最优的基因。
                
                关于遗传算法的详细参数和输出，参见self._search_ga()函数的docstring
            """
            raise NotImplementedError
        elif how == 4:
            """ ANN 人工神经网络
            
            """
            raise NotImplementedError
        elif how == 5:
            """ SVM 支持向量机方法
            
            """
            raise NotImplementedError

        print(f'\n==========SEARCHING FINISHED===============')
        print(f'Searching finished, {len(perfs)} best results are generated')
        print(f'The best parameter performs {perfs[-1]/perfs[0]:.3f} times better than the least performing result')
        print(f'best result: {perfs[-1]:.3f} obtained at parameter: \n{pars[-1]}')
        print(f'least result: {perfs[0]:.3f} obtained at parameter: \n{pars[0]}')
        result_df = pd.DataFrame(perfs, pars)
        print(f'complete list of performance and parameters are following, \n{result_df}')
        print(f'==========OPTIMIZATION COMPLETE============')
        # optimization_log = Log()
        # optimization_log.write_record(pars, perfs)
    elif run_mode == 3:
        """ 进入策略统计预测分析模式
        
        使用蒙特卡洛方法预测策略的未来表现。
        
        """
        raise NotImplementedError


def time_str_format(t: float, estimation: bool = False, short_form: bool = False):
    """ 将int或float形式的时间(秒数)转化为便于打印的字符串格式

    :param t:  输入时间，单位为秒
    :param estimation:
    :param short_form: 时间输出形式，默认为False，输出格式为"XX hour XX day XX min XXsec", 为True时输出"XXD XXH XX'XX".XXX"
    :return:
    """
    assert isinstance(t, float), f'TypeError: t should be a float number, got {type(t)}'
    assert t >= 0, f'ValueError, t should be greater than 0, got minus number'
    # debug
    # print(f'time input is {t}')
    str_element = []
    enough_accuracy = False
    if t >= 86400 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        days = t // 86400
        t = t - days * 86400
        str_element.append(str(int(days)))
        if short_form:
            str_element.append('D')
        else:
            str_element.append('days ')
    if t >= 3600 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        hours = t // 3600
        t = t - hours * 3600
        str_element.append(str(int(hours)))
        if short_form:
            str_element.append('H')
        else:
            str_element.append('hrs ')
    if t >= 60 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        minutes = t // 60
        t = t - minutes * 60
        str_element.append(str(int(minutes)))
        if short_form:
            str_element.append('\'')
        else:
            str_element.append('min ')
    if t >= 1 and not enough_accuracy:
        if estimation:
            enough_accuracy = True
        seconds = np.floor(t)
        t = t - seconds
        str_element.append(str(int(seconds)))
        if short_form:
            str_element.append('\"')
        else:
            str_element.append('s ')
    if not enough_accuracy:
        milliseconds = np.round(t * 1000, 1)
        if short_form:
            str_element.append(f'{int(np.round(milliseconds)):03d}')
        else:
            str_element.append(str(milliseconds))
            str_element.append('ms')

    return ''.join(str_element)


def _get_parameter_performance(par, op, hist, history_list, context) -> float:
    """ 所有优化函数的核心部分，将par传入op中，并给出一个float，代表这组参数的表现评分值performance

    :param par:
    :param op:
    :param hist:
    :param history_list:
    :param context:
    :return: a tuple
    """
    op.set_opt_par(par)  # 设置需要优化的策略参数
    # 生成交易清单并进行模拟交易生成交易记录
    looped_val = apply_loop(op_list=op.create_signal(hist),
                            history_list=history_list,
                            visual=False,
                            cash_plan=context.cash_plan,
                            cost_rate=context.rate,
                            price_visual=False,
                            moq=context.moq)
    # 使用评价函数计算该组参数模拟交易的评价值
    perf = _eval_fv(looped_val)
    return perf


def _progress_bar(prog: int, total: int = 100, comments: str = '', short_form: bool = False):
    """根据输入的数字生成进度条字符串并刷新

    :param prog: 当前进度，用整数表示
    :param total:  总体进度，默认为100
    :param comments:  需要显示在进度条中的文字信息
    :param short_form:  显示
    """
    if prog > total:
        prog = total
    progress_str = f'\r \rOptimization progress: [{PROGRESS_BAR[int(prog / total * 40)]}]' \
                   f' {prog}/{total}. {np.round(prog / total * 100, 1)}%  {comments}'
    sys.stdout.write(progress_str)
    sys.stdout.flush()


def _search_exhaustive(hist, op, context, step_size: [int, tuple], parallel: bool = True):
    """ 最优参数搜索算法1: 穷举法或间隔搜索法

        逐个遍历整个参数空间（仅当空间为离散空间时）的所有点并逐一测试，或者使用某个固定的
        “间隔”从空间中逐个取出所有的点（不管离散空间还是连续空间均适用）并逐一测试，
        寻找使得评价函数的值最大的一组或多组参数

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param context, object, 用于存储优化参数的上下文对象
        :param step_size，int或list，搜索参数，搜索步长，在参数空间中提取参数的间隔，如果是int型，则在空间的每一个轴上
            取同样的步长，如果是list型，则取list中的数字分别作为每个轴的步长
    return: =====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数
    """

    proc_pool = ProcessPoolExecutor()
    pool = ResultPool(context.output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par
    space = Space(s_range, s_type)  # 生成参数空间

    # 使用extract从参数空间中提取所有的点，并打包为iterator对象进行循环
    i = 0
    it, total = space.extract(step_size)
    # debug
    # print('Result pool has been created, capacity of result pool: ', pool.capacity)
    # print('Searching Space has been created: ')
    # space.info()
    # print('Number of points to be checked: ', total)
    # print(f'Historical Data List: \n{hist.info()}')
    # print(f'Cash Plan:\n{context.cash_plan}\nCost Rate:\n{context.rate}')
    # print('Searching Starts...\n')
    history_list = hist.to_dataframe(htype='close').fillna(0)
    st = time.time()
    if parallel:
        # 启用并行计算
        futures = {proc_pool.submit(_get_parameter_performance, par, op, hist, history_list, context): par for par in
                   it}
        for f in as_completed(futures):
            pool.in_pool(futures[f], f.result())
            i += 1
            if i % 10 == 0:
                _progress_bar(i, total)
    else:
        for par in it:
            perf = _get_parameter_performance(par=par,
                                              op=op,
                                              hist=hist,
                                              history_list=history_list,
                                              context=context)
            pool.in_pool(par, perf)
            i += 1
            if i % 10 == 0:
                _progress_bar(i, total)
    # 将当前参数以及评价结果成对压入参数池中，并去掉最差的结果
    # 至于去掉的是评价函数最大值还是最小值，由keep_largest_perf参数确定
    # keep_largest_perf为True则去掉perf最小的参数组合，否则去掉最大的组合
    _progress_bar(i, i)
    pool.cut(context.larger_is_better)
    et = time.time()
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st)}')
    return pool.pars, pool.perfs


def _search_montecarlo(hist, op, context, point_count: int = 50, parallel: bool = True):
    """ 最优参数搜索算法2: 蒙特卡洛法

        从待搜索空间中随机抽取大量的均匀分布的参数点并逐个测试，寻找评价函数值最优的多个参数组合
        随机抽取的参数点的数量为point_count, 输出结果的数量为output_count

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param context, object 用于存储相关参数的上下文对象
        :param point_count，int或list，搜索参数，提取数量，如果是int型，则在空间的每一个轴上
            取同样多的随机值，如果是list型，则取list中的数字分别作为每个轴随机值提取数量目标
    return: =====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数
"""
    proc_pool = ProcessPoolExecutor()
    pool = ResultPool(context.output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par
    space = Space(s_range, s_type)  # 生成参数空间
    # 使用随机方法从参数空间中取出point_count个点，并打包为iterator对象，后面的操作与穷举法一致
    i = 0
    it, total = space.extract(point_count, how='rand')
    # debug
    # print('Result pool has been created, capacity of result pool: ', pool.capacity)
    # print('Searching Space has been created: ')
    # space.info()
    # print('Number of points to be checked:', total)
    # print('Searching Starts...')
    history_list = hist.to_dataframe(htype='close').fillna(0)
    st = time.time()
    if parallel:
        # 启用并行计算
        futures = {proc_pool.submit(_get_parameter_performance, par, op, hist, history_list, context): par for par in
                   it}
        for f in as_completed(futures):
            pool.in_pool(futures[f], f.result())
            i += 1
            if i % 10 == 0:
                _progress_bar(i, total)
    else:
        # 禁用并行计算
        for par in it:
            perf = _get_parameter_performance(par=par,
                                              op=op,
                                              hist=hist,
                                              history_list=history_list,
                                              context=context)
            pool.in_pool(par, perf)
            i += 1
            if i % 10 == 0:
                _progress_bar(i, total)
    pool.cut(context.larger_is_better)
    et = time.time()
    _progress_bar(total, total)
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st, short_form=True)}')
    return pool.pars, pool.perfs


def _search_incremental(hist, op, context, init_step=16, inc_step=2, min_step=1, parallel: bool = True):
    """ 最优参数搜索算法3: 递进搜索法

        该搜索方法的基础还是间隔搜索法，首先通过较大的搜索步长确定可能出现最优参数的区域，然后逐步
        缩小步长并在可能出现最优参数的区域进行“精细搜索”，最终锁定可能的最优参数
        与确定步长的搜索方法和蒙特卡洛方法相比，这种方法能够极大地提升搜索速度，缩短搜索时间，但是
        可能无法找到全局最优参数。同时，这种方法需要参数的评价函数值大致连续

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param context, object, 用于存储交易相关参数的上下文对象
        :param init_step，int，初始步长，默认值为16
        :param inc_step，float，递进系数，每次重新搜索时，新的步长缩小的倍数
        :param min_step，int，终止步长，当搜索步长最小达到min_step时停止搜索
    return: =====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数

"""
    proc_pool = ProcessPoolExecutor()
    pool = ResultPool(context.output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.get_opt_space_par
    spaces = list()  # 子空间列表，用于存储中间结果邻域子空间，邻域子空间数量与pool中的元素个数相同
    base_space = Space(s_range, s_type)
    spaces.append(base_space)  # 将整个空间作为第一个子空间对象存储起来
    step_size = init_step  # 设定初始搜索步长
    history_list = hist.to_dataframe(htype='close').fillna(0)
    round_count = math.log(init_step / min_step) / math.log(inc_step)
    round_size = context.output_count * 5 ** base_space.dim
    first_round_size = base_space.size / init_step ** base_space.dim
    total_calc_rounds = int(first_round_size + round_count * round_size)
    # debug
    # print(f'Result pool prepared, {pool.capacity} total output will be generated')
    # print(f'Base Searching Space has been created: ')
    # base_space.info()
    # print(f'Estimated Total Number of points to be checked:', total_calc_rounds)
    # print('Searching Starts...')
    i = 0
    st = time.time()
    while step_size >= min_step:  # 从初始搜索步长开始搜索，一回合后缩短步长，直到步长小于min_step参数
        while spaces:
            space = spaces.pop()
            # 逐个弹出子空间列表中的子空间，用当前步长在其中搜索最佳参数，所有子空间的最佳参数全部进入pool并筛选最佳参数集合
            it, total = space.extract(step_size, how='interval')
            # debug
            # print(f'Searching the {context.output_count - len(spaces)}th Space from the space list:\n{space.info()}')
            # print(f'{total} points to be checked at step size {step_size}\n')
            if parallel:
                # 启用并行计算
                futures = {proc_pool.submit(_get_parameter_performance, par, op, hist, history_list, context): par for
                           par in it}
                for f in as_completed(futures):
                    pool.in_pool(futures[f], f.result())
                    i += 1
                    if i % 10 == 0:
                        _progress_bar(i, total_calc_rounds, f'step size: {step_size}')
            else:
                # 禁用并行计算
                for par in it:
                    # 以下所有函数都是循环内函数，需要进行提速优化
                    # 以下所有函数在几种优化算法中是相同的，因此可以考虑简化
                    perf = _get_parameter_performance(par=par,
                                                      op=op,
                                                      hist=hist,
                                                      history_list=history_list,
                                                      context=context)
                    pool.in_pool(par, perf)
                    i += 1
                    if i % 20 == 0:
                        _progress_bar(i, total_calc_rounds, f'step size: {step_size}')
        # debug
        # print(f'Completed one round, {pool.item_count} items are put in the Result pool')
        pool.cut(context.larger_is_better)
        # print(f'Cut the pool to reduce its items to capacity, {pool.item_count} items left')
        # 完成一轮搜索后，检查pool中留存的所有点，并生成由所有点的邻域组成的子空间集合
        spaces.append(base_space.from_point(point=item, distance=step_size) for item in pool.pars)
        # 刷新搜索步长
        # debug
        # print(f'{len(spaces)}new spaces created, start next round with new step size', step_size)
        step_size //= inc_step
        _progress_bar(i, total_calc_rounds, f'step size: {step_size}')
    et = time.time()
    _progress_bar(i, i, f'step size: {step_size}')
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st)}')
    return pool.pars, pool.perfs


def _search_ga(hist, op, lpr, output_count, keep_largest_perf):
    """ 最优参数搜索算法4: 遗传算法
    遗传算法适用于在超大的参数空间内搜索全局最优或近似全局最优解，而它的计算量又处于可接受的范围内

    遗传算法借鉴了生物的遗传迭代过程，首先在参数空间中随机选取一定数量的参数点，将这批参数点称为
    “种群”。随后在这一种群的基础上进行迭代计算。在每一次迭代（称为一次繁殖）前，根据种群中每个个体
    的评价函数值，确定每个个体生存或死亡的几率，规律是若个体的评价函数值越接近最优值，则其生存的几率
    越大，繁殖后代的几率也越大，反之则越小。确定生死及繁殖的几率后，根据生死几率选择一定数量的个体
    让其死亡，而从剩下的（幸存）的个体中根据繁殖几率挑选几率最高的个体进行杂交并繁殖下一代个体，
    同时在繁殖的过程中引入随机的基因变异生成新的个体。最终使种群的数量恢复到初始值。这样就完成
    一次种群的迭代。重复上面过程数千乃至数万代直到种群中出现希望得到的最优或近似最优解为止

    input：
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param lpr，object，交易信号回测器对象
        :param output_count，int，输出数量，优化器寻找的最佳参数的数量
        :param keep_largest_perf，bool，True寻找评价分数最高的参数，False寻找评价分数最低的参数
    return: =====tuple对象，包含两个变量
        pool.pars 作为结果输出的参数组
        pool.perfs 输出的参数组的评价分数

"""
    raise NotImplementedError


def _eval_benchmark(looped_value, reference_value, reference_data):
    """ 参考标准年化收益率。具体计算方式为 （(参考标准最终指数 / 参考标准初始指数) ** 1 / 回测交易年数 - 1）

    :param looped_value:
    :param reference_value:
    :return:
    """
    first_day = looped_value.index[0]
    last_day = looped_value.index[-1]
    total_year = (last_day - first_day).days / 365
    rtn_data = reference_value[reference_data]
    rtn = (rtn_data[last_day] / rtn_data[first_day])
    return rtn, rtn ** (1 / total_year) - 1.


def _eval_alpha(looped_val, total_invest, reference_value, reference_data):
    """ 回测结果评价函数：alpha率

    阿尔法。具体计算方式为 (策略年化收益 - 无风险收益) - b × (参考标准年化收益 - 无风险收益)，
    这里的无风险收益指的是中国固定利率国债收益率曲线上10年期国债的年化到期收益率。
    :param looped_val:
    :param total_invest:
    :param reference_value:
    :param reference_data:
    :return:
    """
    first_day = looped_val.index[0]
    last_day = looped_val.index[-1]
    total_year = (last_day - first_day).days / 365
    final_value = _eval_fv(looped_val)
    strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
    reference_return, reference_yearly_return = _eval_benchmark(looped_val, reference_value, reference_data)
    b = _eval_beta(looped_val, reference_value, reference_data)
    return (strategy_return - 0.035) - b * (reference_yearly_return - 0.035)


def _eval_beta(looped_value, reference_value, reference_data):
    """ 贝塔。具体计算方法为 策略每日收益与参考标准每日收益的协方差 / 参考标准每日收益的方差 。

    :param reference_value:
    :param looped_value:
    :return:
    """
    assert isinstance(reference_value, pd.DataFrame)
    ret = looped_value['value'] / looped_value['value'].shift(1)
    ret_dev = ret.std()
    ref = reference_value[reference_data]
    ref_ret = ref / ref.shift(1)
    looped_value['ref'] = ref_ret
    looped_value['ret'] = ret
    return looped_value.ref.cov(looped_value.ret) / ret_dev


def _eval_sharp(looped_val, total_invest, riskfree_interest_rate):
    """ 夏普比率。表示每承受一单位总风险，会产生多少的超额报酬。

    具体计算方法为 (策略年化收益率 - 回测起始交易日的无风险利率) / 策略收益波动率 。

    :param looped_val:
    :return:
    """
    first_day = looped_val.index[0]
    last_day = looped_val.index[-1]
    total_year = (last_day - first_day).days / 365
    final_value = _eval_fv(looped_val)
    strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
    volatility = _eval_volatility(looped_val)
    return (strategy_return - riskfree_interest_rate) / volatility


def _eval_volatility(looped_value):
    """ 策略收益波动率。用来测量资产的风险性。具体计算方法为 策略每日收益的年化标准差 。

    :param looped_value:
    :parma hist_list:
    :return:
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if not looped_value.empty:
        ret = np.log(looped_value['value'] / looped_value['value'].shift(1))
        volatility = ret.rolling(250).std() * np.sqrt(250)
        return volatility[-1]
    else:
        return -np.inf


def _eval_info_ratio(looped_value):
    """ 信息比率。衡量超额风险带来的超额收益。具体计算方法为 (策略每日收益 - 参考标准每日收益)的年化均值 / 年化标准差 。

    :param looped_value:
    :return:
    """
    raise NotImplementedError


def _eval_max_drawdown(looped_value):
    """ 最大回撤。描述策略可能出现的最糟糕的情况。具体计算方法为 max(1 - 策略当日价值 / 当日之前虚拟账户最高价值)

    :param looped_value:
    :return:
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if not looped_value.empty:
        max_val = 0
        max_drawdown = 0
        max_drawdown_date = 0
        for date, value in looped_value.value.iteritems():
            if value > max_val:
                max_val = value
            drawdown = 1 - value / max_val
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_date = date
        return max_drawdown, max_drawdown_date
    else:
        return -np.inf


def _eval_fv(looped_val):
    """评价函数 Future Value 终值评价

'投资模拟期最后一个交易日的资产总值

input:
:param looped_val，ndarray，回测器生成输出的交易模拟记录
return: =====
perf：float，应用该评价方法对回测模拟结果的评价分数

"""
    if not looped_val.empty:
        perf = looped_val['value'][-1]
        return perf
    else:
        return -np.inf


def _eval_operation(op_list, looped_value, cash_plan):
    """ 评价函数，统计操作过程中的基本信息:

    对回测过程进行统计，输出以下内容：
    1，总交易次数：买入操作次数、卖出操作次数
    2，总投资额
    3，总交易费用
    4，回测时间长度

    :param looped_value:
    :param cash_plan:
    :return:
    """
    total_year = np.round((looped_value.index[-1] - looped_value.index[0]).days / 365., 1)
    sell_counts = []
    buy_counts = []
    # 循环统计op_list交易清单中每个个股
    for share, ser in op_list.iteritems():
        # 初始化计数变量
        sell_count = 0
        buy_count = 0
        current_pos = -1
        # 循环统计个股交易清单中的每条交易信号
        for i, value in ser.iteritems():
            if np.sign(value) != current_pos:
                current_pos = np.sign(value)
                if current_pos == 1:
                    buy_count += 1
                else:
                    sell_count += 1
        sell_counts.append(sell_count)
        buy_counts.append(buy_count)
    # 所有统计数字组装成一个DataFrame对象
    op_counts = pd.DataFrame(sell_counts, index=op_list.columns, columns=['sell'])
    op_counts['buy'] = buy_counts
    op_counts['total'] = op_counts.buy + op_counts.sell
    total_op_fee = looped_value.fee.sum()
    total_investment = cash_plan.total
    # 返回所有输出变量
    return total_year, op_counts, total_investment, total_op_fee


def space_around_centre(space, centre, radius, ignore_enums=True):
    """在给定的参数空间中指定一个参数点，并且创建一个以该点为中心且包含于给定参数空间的子空间

    如果参数空间中包含枚举类型维度，可以予以忽略或其他操作
    """
    return space.from_point(point=centre, distance=radius, ignore_enums=ignore_enums)


class ResultPool:
    """结果池类，用于保存限定数量的中间结果，当压入的结果数量超过最大值时，去掉perf最差的结果.

    最初的算法是在每次新元素入池的时候都进行排序并去掉最差结果，这样要求每次都在结果池深度范围内进行排序
    第一步的改进是记录结果池中最差结果，新元素入池之前与最差结果比较，只有优于最差结果的才入池，避免了部分情况下的排序
    新算法在结果入池的循环内函数中避免了耗时的排序算法，将排序和修剪不合格数据的工作放到单独的cut函数中进行，这样只进行一次排序
    新算法将一百万次1000深度级别的排序简化为一次百万级别排序，实测能提速一半左右
    即使在结果池很小，总数据量很大的情况下，循环排序的速度也慢于单次排序修剪
    """

    # result pool operation:
    def __init__(self, capacity):
        """result pool stores all intermediate or final result of searching, the points"""
        self.__capacity = capacity  # 池中最多可以放入的结果数量
        self.__pool = []  # 用于存放中间结果
        self.__perfs = []  # 用于存放每个中间结果的评价分数，老算法仍然使用列表对象

    @property
    def pars(self):
        return self.__pool  # 只读属性，所有池中参数

    @property
    def perfs(self):
        return self.__perfs  # 只读属性，所有池中参数的评价分

    @property
    def capacity(self):
        return self.__capacity

    @property
    def item_count(self):
        return len(self.pars)

    @property
    def is_empty(self):
        return len(self.pars) == 0

    def in_pool(self, item, perf):
        """将新的结果压入池中

        input:
            :param item，object，需要放入结果池的参数对象
            :param perf，float，放入结果池的参数评价分数
        return: =====
            无
        """
        self.__pool.append(item)  # 新元素入池
        self.__perfs.append(perf)  # 新元素评价分记录

    def cut(self, keep_largest=True):
        """将pool内的结果排序并剪切到capacity要求的大小

        直接对self对象进行操作，排序并删除不需要的结果
        input:
            :param keep_largest， bool，True保留评价分数最高的结果，False保留评价分数最低的结果
        return: =====
            无
        """
        poo = self.__pool  # 所有池中元素
        per = self.__perfs  # 所有池中元素的评价分
        cap = self.__capacity
        if keep_largest:
            arr = np.array(per).argsort()[-cap:]
        else:
            arr = np.array(per).argsort()[:cap]
        poo2 = [poo[i] for i in arr]
        per2 = [per[i] for i in arr]
        self.__pool = poo2
        self.__perfs = per2


# TODO: this function can be merged with str_to_list() in history.py
def input_to_list(pars: [str, int, list], dim: int, padder=None):
    """将输入的参数转化为List，同时确保输出的List对象中元素的数量至少为dim，不足dim的用padder补足

    input:
        :param pars，需要转化为list对象的输出对象
        :param dim，需要生成的目标list的元素数量
        :param padder，当元素数量不足的时候用来补充的元素
    return: =====
        pars, list 转化好的元素清单
    """
    if isinstance(pars, (str, int, np.int64)):  # 处理字符串类型的输入
        # print 'type of types', type(pars)
        pars = [pars] * dim
    else:
        pars = list(pars)  # 正常处理，输入转化为列表类型
    par_dim = len(pars)
    # 当给出的两个输入参数长度不一致时，用padder补齐type输入，或者忽略多余的部分
    if par_dim < dim:
        pars.extend([padder] * (dim - par_dim))
    return pars


class Space:
    """定义一个参数空间，一个参数空间包含一个或多个Axis对象，存储在axes列表中

    参数空间类用于生成并管理一个参数空间，从参数空间中根据一定的要求提取出一系列的参数点并组装成迭代器供优化器调用
    参数空间包含一个或多个轴，每个轴代表参数空间的一个维度，从每个轴上取出一个数值作为参数空间中某个点的坐标，而这个坐标
    就代表空间中的一个参数组合
    参数空间支持三种不同的轴，整数轴、浮点轴，这两种都是数值型的轴，还有另一种枚举轴，包含不同对象的枚举，同样可以作为参数
    空间的一个维度独立存在，与数值轴的操作方式相同
    数值轴的定义方式为上下界定义，枚举轴的定义方式为枚举定义，数值轴的取值范围为上下界之间的合法数值，而枚举轴的取值为枚举
    列表中的值
    """

    def __init__(self, pars, par_types: [list, str] = None):
        """参数空间对象初始化，根据输入的参数生成一个空间

        input:
            :param pars，int、float或list,需要建立参数空间的初始信息，通常为一个数值轴的上下界，如果给出了types，按照
                types中的类型字符串创建不同的轴，如果没有给出types，系统根据不同的输入类型动态生成的空间类型分别如下：
                    pars为float，自动生成上下界为(0, pars)的浮点型数值轴，
                    pars为int，自动生成上下界为(0, pars)的整形数值轴
                    pars为list，根据list的元素种类和数量生成不同类型轴：
                        list元素只有两个且元素类型为int或float：生成上下界为(pars[0], pars[1])的浮点型数值
                        轴或整形数值轴
                        list元素不是两个，或list元素类型不是int或float：生成枚举轴，轴的元素包含par中的元素
            :param par_types，list，默认为空，生成的空间每个轴的类型，如果给出types，应该包含每个轴的类型字符串：
                'discr': 生成整数型轴
                'conti': 生成浮点数值轴
                'enum': 生成枚举轴
        return: =====
            无
        """
        self._axes = []
        # 处理输入，将输入处理为列表，并补齐与dim不足的部分
        pars = list(pars)
        par_dim = len(pars)
        # debug
        # print('par types before processing:', par_types)
        if par_types is None:
            par_types = []
        elif isinstance(par_types, str):
            par_types = str_to_list(par_types, ',')
        par_types = input_to_list(par_types, par_dim, None)
        # debug：
        # print('par dim:', par_dim)
        # print('pars and par_types:', pars, par_types)
        # 逐一生成Axis对象并放入axes列表中
        for i in range(par_dim):
            # print('appending', i+1, '-th par', pars[i],'in type:', par_types[i])
            self._axes.append(Axis(pars[i], par_types[i]))

    @property
    def dim(self):  # 空间的维度
        return len(self._axes)

    @property
    def types(self):
        """List of types of axis of the space"""
        if self.dim > 0:
            types = [self._axes[i].axis_type for i in range(self.dim)]
            return types
        else:
            return None

    @property
    def boes(self):
        """List of bounds of axis of the space"""
        if self.dim > 0:
            boes = [self._axes[i].axis_boe for i in range(self.dim)]
            return boes
        else:
            return None

    @property
    def shape(self):
        """输出空间的维度大小，输出形式为元组，每个元素代表对应维度的元素个数"""
        s = [axis.count for axis in self._axes]
        return tuple(s)

    @property
    def size(self):
        """输出空间的尺度，输出每个维度的跨度之乘积"""
        s = [axis.size for axis in self._axes]
        return np.product(s)

    @property
    def count(self):
        s = [axis.count for axis in self._axes]
        return np.product(s)

    def info(self):
        """打印空间的各项信息"""
        if self.dim > 0:
            print(type(self))
            print('dimension:', self.dim)
            print('types:', self.types)
            print('the bounds or enums of space', self.boes)
            print('shape of space:', self.shape)
            print('size of space:', self.size)
        else:
            print('Space is empty!')

    def extract(self, interval_or_qty: int = 1, how: str = 'interval'):
        """从空间中提取出一系列的点，并且把所有的点以迭代器对象的形式返回供迭代

        input:
            :param interval_or_qty: int。从空间中每个轴上需要提取数据的步长或坐标数量
            :param how, str, 有两个合法参数：
                'interval',以间隔步长的方式提取坐标，这时候interval_or_qty代表步长
                'rand', 以随机方式提取坐标，这时候interval_or_qty代表提取数量
        return: tuple，包含两个数据
            iter，迭代器数据，打包好的所有需要被提取的点的集合
            total，int，迭代器输出的点的数量
        """
        interval_or_qty_list = input_to_list(pars=interval_or_qty,
                                             dim=self.dim,
                                             padder=[1])
        axis_ranges = []
        i = 0
        total = 1
        for axis in self._axes:  # 分别从各个Axis中提取相应的坐标
            axis_ranges.append(axis.extract(interval_or_qty_list[i], how))
            total *= len(axis_ranges[i])
            i += 1
        if how == 'interval':
            return itertools.product(*axis_ranges), total  # 使用迭代器工具将所有的坐标乘积打包为点集
        elif how == 'rand':
            return itertools.zip_longest(*axis_ranges), interval_or_qty  # 使用迭代器工具将所有点组合打包为点集

    def __contains__(self, point: [list, tuple]):
        """ 判断item是否在Space对象中, 返回True如果item在Space中，否则返回False

        :param point:
        :return: bool
        """
        assert isinstance(point, (list, tuple)), \
            f'TypeError, a point in a space must be in forms of a tuple or a list, got {type(point)}'
        if len(point) != self.dim:
            return False
        for coordinate, boe, type in zip(point, self.boes, self.types):
            if type == 'enum':
                if not coordinate in boe:
                    return False
            else:
                if not boe[0] < coordinate < boe[1]:
                    return False
        return True

    def from_point(self, point, distance: [int, float, list], ignore_enums=True):
        """在已知空间中以一个点为中心点生成一个字空间

        input:
            :param point，object，已知参数空间中的一个参数点
            :param distance， int或float，需要生成的新的子空间的数轴半径
            :param ignore_enums，bool，True忽略enum型轴，生成的子空间包含枚举型轴的全部元素，False生成的子空间
                包含enum轴的部分元素
        return: =====

        """
        assert point in self, f'ValueError, point {point} is not in space!'
        assert self.dim > 0, 'original space should not be empty!'
        assert isinstance(distance, (int, float, list)), \
            f'TypeError, the distance must be a number of a list of numbers, got {type(distance)} instead'
        pars = []
        if isinstance(distance, list):
            assert len(distance) == self.dim, \
                f'ValueError, can not match {len(distance)} distances in {self.dim} dimensions!'
        else:
            distance = [distance] * self.dim
        for coordinate, boe, type, dis in zip(point, self.boes, self.types, distance):
            if type != 'enum':
                space_lbound = boe[0]
                space_ubound = boe[1]
                lbound = max((coordinate - dis), space_lbound)
                ubound = min((coordinate + dis), space_ubound)
                pars.append((lbound, ubound))
            else:
                if ignore_enums:
                    pars.append(boe)
                else:
                    enum_pos = boe.index(coordinate)
                    lbound = max((enum_pos - dis), 0)
                    ubound = min((enum_pos + dis), len(boe))
                    pars.append(boe[lbound:ubound])
        return Space(pars, self.types)


class Axis:
    """数轴对象，空间对象的一个组成部分，代表空间对象的一个维度


    """

    def __init__(self, bounds_or_enum, typ=None):
        self._axis_type = None  # 数轴类型
        self._lbound = None  # 离散型或连续型数轴下界
        self._ubound = None  # 离散型或连续型数轴上界
        self._enum_val = None  # 当数轴类型为“枚举”型时，储存改数轴上所有可用值
        # 将输入的上下界或枚举转化为列表，当输入类型为一个元素时，生成一个空列表并添加该元素
        boe = list(bounds_or_enum)
        length = len(boe)  # 列表元素个数
        # debug
        # print('in Axis: boe recieved, and its length:', boe, length, 'type of boe:', typ)
        if typ is None:
            # 当typ为空时，需要根据输入数据的类型猜测typ
            if length <= 2:  # list长度小于等于2，根据数据类型取上下界，int产生离散，float产生连续
                if isinstance(boe[0], int):
                    typ = 'discr'
                elif isinstance(boe[0], float):
                    typ = 'conti'
                else:  # 输入数据类型不是数字时，处理为枚举类型
                    typ = 'enum'
            else:  # list长度为其余值时，全部处理为enum数据
                typ = 'enum'
        elif typ != 'enum' and typ != 'discr' and typ != 'conti':
            typ = 'enum'  # 当发现typ为异常字符串时，修改typ为enum类型
        # debug
        # print('in Axis, after infering typ, the typ is:', typ)
        # 开始根据typ的值生成具体的Axis
        if typ == 'enum':  # 创建一个枚举数轴
            self._new_enumerate_axis(boe)
        elif typ == 'discr':  # 创建一个离散型数轴
            if length == 1:
                self._new_discrete_axis(0, boe[0])
            else:
                self._new_discrete_axis(boe[0], boe[1])
        else:  # 创建一个连续型数轴
            if length == 1:
                self._new_continuous_axis(0, boe[0])
            else:
                self._new_continuous_axis(boe[0], boe[1])

    @property
    def count(self):
        """输出数轴中元素的个数，若数轴为连续型，输出为inf"""
        self_type = self._axis_type
        if self_type == 'conti':
            return np.inf
        elif self_type == 'discr':
            return self._ubound - self._lbound
        else:
            return len(self._enum_val)

    @property
    def size(self):
        """输出数轴的跨度，或长度，对连续型数轴来说，定义为上界减去下界"""
        self_type = self._axis_type
        if self_type == 'conti':
            return self._ubound - self._lbound
        else:
            return self.count

    @property
    def axis_type(self):
        """返回数轴的类型"""
        return self._axis_type

    @property
    def axis_boe(self):
        """返回数轴的上下界或枚举"""
        if self._axis_type == 'enum':
            return tuple(self._enum_val)
        else:
            return self._lbound, self._ubound

    def extract(self, interval_or_qty=1, how='interval'):
        """从数轴中抽取数据，并返回一个iterator迭代器对象

        input:
            :param interval_or_qty: int 需要从数轴中抽取的数据总数或抽取间隔，当how=='interval'时，代表抽取间隔，否则代表总数
            :param how: str 抽取方法，'interval' 或 'rand'， 默认'interval'
        return:
            一个迭代器对象，包含所有抽取的数值
        """
        if how == 'interval':
            if self.axis_type == 'enum':
                return self._extract_enum_interval(interval_or_qty)
            else:
                return self._extract_bounding_interval(interval_or_qty)
        else:
            if self.axis_type == 'enum':
                return self._extract_enum_random(interval_or_qty)
            else:
                return self._extract_bounding_random(interval_or_qty)

    def _set_bounds(self, lbound, ubound):
        """设置数轴的上下界, 只适用于离散型或连续型数轴

        input:
            :param lbound int/float 数轴下界
            :param ubound int/float 数轴上界
        return:
            None
        """
        self._lbound = lbound
        self._ubound = ubound
        self.__enum = None

    def _set_enum_val(self, enum):
        """设置数轴的枚举值，适用于枚举型数轴

        input:
            :param enum: 数轴枚举值
        :return:
            None
        """
        self._lbound = None
        self._ubound = None
        self._enum_val = np.array(enum, subok=True)

    def _new_discrete_axis(self, lbound, ubound):
        """ 创建一个新的离散型数轴

        input:
            :param lbound: 数轴下界
            :param ubound: 数轴上界
        :return:
            None
        """
        self._axis_type = 'discr'
        self._set_bounds(int(lbound), int(ubound))

    def _new_continuous_axis(self, lbound, ubound):
        """ 创建一个新的连续型数轴

        input:
            :param lbound: 数轴下界
            :param ubound: 数轴上界
        :return:
            None
        """
        self._axis_type = 'conti'
        self._set_bounds(float(lbound), float(ubound))

    def _new_enumerate_axis(self, enum):
        """ 创建一个新的枚举型数轴

        input:
            :param enum: 数轴的枚举值
        :return:
        """
        self._axis_type = 'enum'
        self._set_enum_val(enum)

    def _extract_bounding_interval(self, interval):
        """ 按照间隔方式从离散或连续型数轴中提取值

        input:
            :param interval: 提取间隔
        :return:
            np.array 从数轴中提取出的值对象
        """
        return np.arange(self._lbound, self._ubound, interval)

    def _extract_bounding_random(self, qty: int):
        """ 按照随机方式从离散或连续型数轴中提取值

        input:
            :param qty: 提取的数据总量
        :return:
            np.array 从数轴中提取出的值对象
        """
        if self._axis_type == 'discr':
            result = np.random.randint(self._lbound, self._ubound + 1, size=qty)
        else:
            result = self._lbound + np.random.random(size=qty) * (self._ubound - self._lbound)
        return result

    def _extract_enum_interval(self, interval):
        """ 按照间隔方式从枚举型数轴中提取值

        input:
            :param interval: 提取间隔
        :return:
            list 从数轴中提取出的值对象
        """
        count = self.count
        return self._enum_val[np.arange(0, count, interval)]

    def _extract_enum_random(self, qty: int):
        """ 按照随机方式从枚举型数轴中提取值

        input:
            :param qty: 提取间隔
        :return:
            list 从数轴中提取出的值对象
        """
        count = self.count
        return self._enum_val[np.random.choice(count, size=qty)]