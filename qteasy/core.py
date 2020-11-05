# coding=utf-8
# core.py

# ======================================
# This file contains core functions and
# core Classes. Such as looping and
# optimizations, Contexts and Spaces, etc.
# ======================================

import pandas as pd
import numpy as np
import datetime
import time
import math

from concurrent.futures import ProcessPoolExecutor, as_completed

from .history import get_history_panel, HistoryPanel
from .utilfuncs import time_str_format, progress_bar
from .space import Space
from .finance import Cost, CashPlan
from .operator import Operator
from .visual import plot_loop_result


AVAILABLE_EVALUATION_INDICATORS = []

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


# TODO: Usability improvements:
# TODO: 1: 增加PREDICT模式，完善predict模式所需的参数，完善其他优化算法的参数
# TODO: 2: 取消Context类，采用config字典的形式处理所有的qt.run()参数。借鉴
# TODO:     matplotlib.finance的处理方法，将所有的参数内容都以**kwargs
# TODO:     的形式传入qt.run()方法，使用config字典来获取所有的参数。使用
# TODO:     _valid_qt_args()函数来保存并设置所有可用的参数以及他们的验证方法
# TODO: 使用_validate_qt_args()方法来对所有的参数进行验证，在qt.run()中调用config字典，使用config字典中的参数来控制qt的行为。
# TODO: 提供config参数的保存和显示功能，设置所有参数的显示级别，确保按照不同级别显示不同的config参数
# TODO: 在run()中增加基本args确认功能，在运行之前确认不会缺乏必要的参数
# TODO: 完善context对象的信息属性，使得用户可以快速了解当前配置
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

            opti_start:                 str, 优化历史区间起点，默认值'20050106'
            opti_end:                   str, 优化历史区间终点，默认值'20141231'
            opti_window_count:          int, 当选择多重优化区间时，优化历史区间的数量，默认值=1
            opti_window_offset:         str, 当选择多重优化区间时，不同区间的开始间隔，默认值='1Y'
            opti_weighting_type:        int 当选择多重优化区间时，计算平均表现分数的方法：
                                        {0: 简单平均值,
                                         1: 线性加权平均值,
                                         2: 指数加权平均值}

            test_period_type:           int, 参数测试区间类型，在一段历史数据区间上找到最优参数后，可以在同一个区间上测试最优参数的
                                        表现，也可以在不同的历史数据区间上测试（这是更好的办法），选项有三个：
                                        {0: 相同区间, 此情况下忽略test_start与test_end参数，使用opti_start与opti_end,
                                         1: 接续区间, 此情况下忽略test_start与test_end参数，使用
                                                    opti_end与opti_end+opti_end-opti_start
                                         2: 自定义区间}
                                         默认值=2

            test_start:                 str, 如果选择自定义区间，测试区间与寻优区间之间的间隔
            test_end:                   str, 测试历史区间跨度
            target_function:            str, 作为优化目标的评价函数
            maximize_result:            bool, 确定目标函数的优化方向，保留函数值最大的还是最小的结果，默认True，寻找函数值最大的结果

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
        self._invest_dates = '20060403'
        self._invest_amounts = [10000]
        self.cash_plan = CashPlan(self._invest_dates, self._invest_amounts)

        self.fixed_buy_fee = 5
        self.fixed_sell_fee = 0
        self.fixed_buy_rate = 0.0035
        self.fixed_sell_rate = 0.0015
        self.min_buy_fee = 5
        self.min_sell_fee = 5
        self.slippage = 0
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

        self.opti_start = '20040506'
        self.opti_end = '20141231'
        self.opti_window_count = 1
        self.opti_window_offset = '1Y'
        self.opti_weighting_type = 0
        self.opti_cash_plan = CashPlan(dates='20060403', amounts=10000)

        self.test_period_type = 2

        self.test_start = '20120604'
        self.test_end = '20201231'
        self.test_cash_plan = CashPlan(dates='20140106', amounts=10000)
        self.target_function = 'FV'
        self.maximize_result = True

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
    def invest_amounts(self):
        return self.cash_plan.amounts

    @invest_amounts.setter
    def invest_amounts(self, amounts):
        try:
            self.cash_plan = CashPlan(dates=self._invest_dates, amounts=amounts)
        except:
            raise ValueError(f'Your input does not fit the invest dates')

    @property
    def invest_dates(self):
        return [day.strftime('%Y%m%d') for day in self.cash_plan.dates]

    @invest_dates.setter
    def invest_dates(self, dates):
        try:
            self.cash_plan = CashPlan(dates=dates, amounts=self._invest_amounts)
        except:
            raise ValueError(f'Your input does not fit the invest amounts')


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
        print(f'本期期初总资产: {pre_value:.2f}，其中包括: \n期初现金: {pre_cash:.2f}, \n'
              f'期初持有资产: {np.round(pre_amounts, 2)}\n且资产价格为: {np.round(prices, 2)}')
        print(f'本期交易信号{np.round(op, 2)}')
    # 计算按照交易清单出售资产后的资产余额以及获得的现金
    # 根据出售持有资产的份额数量计算获取的现金
    amount_sold, cash_gained, fee_selling = rate.get_selling_result(prices=prices,
                                                                    op=op,
                                                                    amounts=pre_amounts)
    if print_log:
        print(f'以本期资产价格{np.round(prices, 2)}出售资产 {np.round(-amount_sold, 2)}')
        print(f'获得现金:{cash_gained:.2f}, 产生交易费用 {fee_selling:.2f}, 交易后现金余额: {(pre_cash + cash_gained):.3f}')
    # 本期出售资产后现金余额 = 期初现金余额 + 出售资产获得现金总额
    cash = pre_cash + cash_gained
    # 初步估算按照交易清单买入资产所需要的现金，如果超过持有现金，则按比例降低买入金额
    pur_values = pre_value * op.clip(0)  # 使用clip来代替np.where，速度更快,且op.clip(1)比np.clip(op, 0, 1)快很多
    if print_log:
        print(f'本期计划买入资产动用资金: {pur_values.sum():.2f}')
    if pur_values.sum() > cash:
        # 估算买入资产所需现金超过持有现金
        pur_values = pur_values / pur_values.sum() * cash
        if print_log:
            print(f'由于持有现金不足，调整动用资金数量为: {pur_values.sum():.2f}')
            # 按比例降低分配给每个拟买入资产的现金额度
    # 计算购入每项资产实际花费的现金以及实际买入资产数量，如果MOQ不为0，则需要取整并修改实际花费现金额
    amount_purchased, cash_spent, fee_buying = rate.get_purchase_result(prices=prices,
                                                                        op=op,
                                                                        pur_values=pur_values,
                                                                        moq=moq)
    if print_log:
        print(f'以本期资产价格{np.round(prices, 2)}买入资产 {np.round(amount_purchased, 2)}')
        print(f'实际花费现金 {cash_spent:.2f} 并产生交易费用: {fee_buying:.2f}')
    # 计算购入资产产生的交易成本，买入资产和卖出资产的交易成本率可以不同，且每次交易动态计算
    fee = fee_buying + fee_selling
    # 持有资产总额 = 期初资产余额 + 本期买入资产总额 + 本期卖出资产总额（负值）
    amounts = pre_amounts + amount_purchased + amount_sold
    # 期末现金余额 = 本期出售资产后余额 + 本期购入资产花费现金总额（负值）
    cash += cash_spent.sum()
    # 期末资产总价值 = 期末资产总额 * 本期资产单价 + 期末现金余额
    value = (amounts * prices).sum() + cash
    if print_log:
        print(f'期末现金: {cash:.2f}, 期末总资产: {value:.2f}\n')
    return cash, amounts, fee, value


def _get_complete_hist(looped_value: pd.DataFrame,
                       h_list: pd.DataFrame,
                       ref_list: pd.DataFrame,
                       with_price: bool = False) -> pd.DataFrame:
    """完成历史交易回测后，填充完整的历史资产总价值清单，
        同时在回测清单中填入参考价格数据，参考价格数据用于数据可视化对比，参考数据的来源为context.reference_asset

    input:=====
        :param values：完成历史交易回测后生成的历史资产总价值清单，只有在操作日才有记录，非操作日没有记录
        :param h_list：完整的投资产品价格清单，包含所有投资产品在回测区间内每个交易日的价格
        :param ref_list: 参考资产的历史价格清单，参考资产用于收益率的可视化对比，同时用于计算alpha、sharp等指标
        :param with_price：Bool，True时在返回的清单中包含历史价格，否则仅返回资产总价值
    return: =====
        values，pandas.DataFrame：重新填充的完整历史交易日资产总价值清单
    """
    # 获取价格清单中的投资产品列表
    shares = h_list.columns  # 获取资产清单
    start_date = looped_value.index[0]  # 开始日期
    looped_history = h_list.loc[start_date:]  # 回测历史数据区间 = [开始日期:]
    # 使用价格清单的索引值对资产总价值清单进行重新索引，重新索引时向前填充每日持仓额、现金额，使得新的
    # 价值清单中新增的记录中的持仓额和现金额与最近的一个操作日保持一致，并消除nan值
    purchased_shares = looped_value[shares].reindex(looped_history.index, method='ffill').fillna(0)
    cashes = looped_value['cash'].reindex(looped_history.index, method='ffill').fillna(0)
    fees = looped_value['fee'].reindex(looped_history.index).fillna(0)
    looped_value = looped_value.reindex(looped_history.index)
    # 这里采用了一种看上去貌似比较奇怪的处理方式：
    # 先为cashes、purchased_shares两个变量赋值，
    # 然后再将上述两个变量赋值给looped_values的列中
    # 这样看上去好像多此一举，为什么不能直接赋值，然而
    # 经过测试，如果直接用下面的代码直接赋值，将无法起到
    # 填充值的作用：
    # looped_value.cash = looped_value.cash.reindex(dates, method='ffill')
    looped_value[shares] = purchased_shares
    looped_value.cash = cashes
    looped_value.fee = looped_value['fee'].reindex(looped_history.index).fillna(0)
    looped_value['reference'] = ref_list.reindex(looped_history.index).fillna(0)
    # print(f'extended looped value according to looped history: \n{looped_value.info()}')
    # 重新计算整个清单中的资产总价值，生成pandas.Series对象
    looped_value['value'] = (looped_history * looped_value[shares]).sum(axis=1) + looped_value['cash']
    if with_price:  # 如果需要同时返回价格，则生成pandas.DataFrame对象，包含所有历史价格
        share_price_column_names = [name + '_p' for name in shares]
        looped_value[share_price_column_names] = looped_history[shares]
    # print(looped_value.tail(10))
    return looped_value


def _merge_invest_dates(op_list: pd.DataFrame, invest: CashPlan) -> pd.DataFrame:
    """将完成的交易信号清单与现金投资计划合并：
        检查现金投资计划中的日期是否都存在于交易信号清单op_list中，如果op_list中没有相应日期时，当交易信号清单中没有相应日期时，添加空交易
        信号，以便使op_list中存在相应的日期。

        注意，在目前的设计中，要求invest中的所有投资日期都为交易日（意思是说，投资日期当天资产价格不为np.nan）
        否则，将会导致回测失败（回测当天取到np.nan作为价格，引起总资产计算失败，引起连锁反应所有的输出结果均为np.nan。

        需要在CashPlan投资计划类中增加合法性判断

    :param op_list: 交易信号清单，一个DataFrame。index为Timestamp类型
    :param invest: CashPlan对象，投资日期和投资金额
    :return:
    """
    if not isinstance(op_list, pd.DataFrame):
        raise TypeError(f'operation list should be a pandas DataFrame, got {type(op_list)} instead')
    if not isinstance(invest, CashPlan):
        raise TypeError(f'invest plan should be a qteasy CashPlan, got {type(invest)} instead')
    # debug
    # print(f'in function merge_invest_dates, got op_list BEFORE merging:\n{op_list}\n'
    #       f'will merge following dates into op_list:\n{invest.dates}')
    for date in invest.dates:
        try:
            op_list.loc[date]
        except:
            op_list.loc[date] = 0
    # debug
    # print(f'in function merge_invest_dates, got op_list AFTER merging:\n{op_list}')
    op_list.sort_index(inplace=True)
    # debug
    # print(f'in function merge_invest_dates, got op_list AFTER merging:\n{op_list}')
    return op_list


# TODO: 并将过程和信息输出到log文件或log信息中，返回log信息
def apply_loop(op_list: pd.DataFrame,
               history_list: pd.DataFrame,
               cash_plan: CashPlan = None,
               cost_rate: Cost = None,
               moq: float = 100.,
               inflation_rate: float = 0.03,
               print_log: bool = False) -> pd.DataFrame:
    """使用Numpy快速迭代器完成整个交易清单在历史数据表上的模拟交易，并输出每次交易后持仓、
        现金额及费用，输出的结果可选

    input：=====
        :param cash_plan: float: 初始资金额，未来将被替换为CashPlan对象
        :param history_list: object pd.DataFrame: 完整历史价格清单，数据的频率由freq参数决定
        :param op_list: object pd.DataFrame: 标准格式交易清单，描述一段时间内的交易详情，每次交易一行数据
        :param cost_rate: float Rate: 交易成本率对象，包含交易费、滑点及冲击成本
        :param moq: float：每次交易的最小份额单位
        :param inflation_rate: float, 现金的时间价值率，如果>0，则现金的价值随时间增长，增长率为inflation_rate
        :param print_log: bool: 设置为True将打印回测详细日志

    output：=====
        Value_history: pandas.DataFrame: 包含交易结果及资产总额的历史清单

    """
    assert not op_list.empty, 'InputError: The Operation list should not be Empty'
    assert cost_rate is not None, 'TypeError: cost_rate should not be None type'
    assert cash_plan is not None, 'ValueError: cash plan should not be None type'

    # 根据最新的研究实验，在python3.6的环境下，nditer的速度显著地慢于普通的for-loop
    # 因此改回for-loop执行，直到找到更好的向量化执行方法
    # 提取交易清单中的所有数据，生成np.ndarray，即所有的交易信号
    op_list = _merge_invest_dates(op_list, cash_plan)
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
    # print(f'op list is loaded, op list head is \n{op_list.head(5)}')
    # print(f'finding cash investment date position: finding: \n{cash_plan.dates} \nin looped dates (first 3):\n '
    #       f'{looped_dates[0:3]}'
    #       f', got result:\n{investment_date_pos}')
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
        cash, amounts, fee, value = _loop_step(pre_cash=cash,
                                               pre_amounts=amounts,
                                               op=op[i],
                                               prices=price[i],
                                               rate=cost_rate,
                                               moq=moq,
                                               print_log=print_log)
        # 保存计算结果
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
    return value_history


def get_current_holdings() -> tuple:
    """ 获取当前持有的产品在手数量

    :return: tuple:
    """
    raise NotImplementedError


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
    print(f'====================================\n'
          f'       RUNNING IN MODE {run_mode}\n'
          f'      --{run_mode_text}--\n'
          f'====================================\n')

    # 根据根据operation对象和context对象的参数生成不同的历史数据用于不同的用途：
    # 用于交易信号生成的历史数据
    # TODO: 生成的历史数据还应该基于更多的参数，比如采样频率、以及提前期等
    # 生成用于数据回测的历史数据
    if run_mode <= 1:
        hist_op = get_history_panel(start=context.invest_start,
                                    end=context.invest_end,
                                    shares=context.share_pool,
                                    htypes=operator.op_data_types,
                                    freq=operator.op_data_freq,
                                    asset_type=context.asset_type,
                                    chanel='online')
        # 生成用于数据回测的历史数据，格式为pd.DataFrame，仅有一个价格数据用于计算交易价格
        hist_loop = hist_op.to_dataframe(htype='close')

    if run_mode == 2:
        # 生成用于策略优化训练的训练历史数据集合
        hist_opti = get_history_panel(start=context.opti_start,
                                      end=context.opti_end,
                                      shares=context.share_pool,
                                      htypes=operator.op_data_types,
                                      freq=operator.op_data_freq,
                                      asset_type=context.asset_type,
                                      chanel='online')
        # 生成用于优化策略测试的测试历史数据集合
        hist_test = get_history_panel(start=context.test_start,
                                      end=context.test_end,
                                      shares=context.share_pool,
                                      htypes=operator.op_data_types,
                                      freq=operator.op_data_freq,
                                      asset_type=context.asset_type,
                                      chanel='online')
        hist_test_loop = hist_test.to_dataframe(htype='close')

    # 生成参考历史数据，作为参考用于回测结果的评价
    hist_reference = (get_history_panel(start=context.invest_start,
                                        end=context.invest_end,
                                        shares=context.reference_asset,
                                        htypes=context.reference_data_type,
                                        freq=operator.op_data_freq,
                                        asset_type=context.reference_asset_type,
                                        chanel='online')
                      ).to_dataframe(htype='close')
    # debug
    # print(f'operation hist data downloaded, info: \n')
    # hist_op.info()
    # print(f'optimization hist data downloaded, info: \n')
    # hist_opti.info()
    # print(f'test hist data downloaded, info: \n')
    # hist_test.info()
    # print(f'reference hist data downloaded, info: \n')
    # hist_reference.info()

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
        print(f'====================================\n'
              f'|                                  |\n'
              f'|       OPERATION SIGNALS          |\n'
              f'|                                  |\n'
              f'====================================\n')
        print(f'time consumption for operate signal creation: {time_str_format(run_time_prepare_data)}\n')
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
                                   history_list=hist_loop,
                                   cash_plan=context.cash_plan,
                                   moq=context.moq,
                                   cost_rate=context.rate,
                                   print_log=context.print_log)
        et = time.time()
        run_time_loop_full = (et - st)
        # 对回测的结果进行基本评价（回测年数，操作次数、总投资额、总交易费用（成本）
        years, oper_count, total_invest, total_fee = _eval_operation(op_list=op_list,
                                                                     looped_value=looped_values,
                                                                     cash_plan=context.cash_plan)
        # 评价回测结果——计算回测终值
        final_value = _eval_fv(looped_val=looped_values)
        # 评价回测结果——计算总投资收益率
        ret = final_value / total_invest
        # 评价回测结果——计算最大回撤比例以及最大回撤发生日期
        mdd, max_date, low_date = _eval_max_drawdown(looped_values)
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
        # 评价回测结果——计算投资回报的信息比率
        info = _eval_info_ratio(looped_values, hist_reference, reference_data)
        if context.visual:
            # 图表输出投资回报历史曲线
            complete_value = _get_complete_hist(looped_value=looped_values,
                                                h_list=hist_loop,
                                                ref_list=hist_reference,
                                                with_price=False)
            # TODO: above performance indicators should be also printed on the plot,
            # TODO: thus users can choose either plain text report or a chart report.
            performance_dict = {'run_time_p': run_time_prepare_data,
                                'run_time_l': run_time_loop_full,
                                'loop_start': looped_values.index[0],
                                'loop_end': looped_values.index[-1],
                                'years': years,
                                'oper_count': oper_count,
                                'total_invest': total_invest,
                                'total_fee': total_fee,
                                'final_value': final_value,
                                'rtn': ret - 1,
                                'mdd': mdd,
                                'max_date': max_date,
                                'low_date': low_date,
                                'volatility': volatility,
                                'ref_rtn': ref_rtn,
                                'ref_annual_rtn': ref_annual_rtn,
                                'beta': beta,
                                'sharp': sharp,
                                'alpha': alpha,
                                'info': info}
            plot_loop_result(complete_value, msg=performance_dict)
        else:
            # 格式化输出回测结果
            print(f'==================================== \n'
                  f'|                                  |\n'
                  f'|       BACK TESTING RESULT        |\n'
                  f'|                                  |\n'
                  f'====================================')
            print(f'\nqteasy running mode: 1 - History back looping\n'
                  f'time consumption for operate signal creation: {time_str_format(run_time_prepare_data)} ms\n'
                  f'time consumption for operation back looping: {time_str_format(run_time_loop_full)} ms\n')
            print(f'investment starts on {looped_values.index[0]}\nends on {looped_values.index[-1]}\n'
                  f'Total looped periods: {years} years.')
            print(f'operation summary:\n {oper_count}\nTotal operation fee:     ¥{total_fee:13,.2f}')
            print(f'total investment amount: ¥{total_invest:13,.2f}\n'
                  f'final value:             ¥{final_value:13,.2f}')
            print(f'Total return: {ret * 100 - 100:.3f}% \n'
                  f'Average Yearly return rate: {(ret ** (1 / years) - 1) * 100: .3f}%')
            print(f'Total reference return: {ref_rtn * 100:.3f}% \n'
                  f'Average Yearly reference return rate: {ref_annual_rtn * 100:.3f}%')
            print(f'strategy performance indicators: \n'
                  f'alpha:               {alpha:.3f}\n'
                  f'Beta:                {beta:.3f}\n'
                  f'Sharp ratio:         {sharp:.3f}\n'
                  f'Info ratio:          {info:.3f}\n'
                  f'250 day volatility:  {volatility:.3f}\n'
                  f'Max drawdown:        {mdd * 100:.3f}% from {max_date.date()} to {low_date.date()}')
            print(f'\n===========END OF REPORT=============\n')
        return sharp
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
        operator.prepare_data(hist_data=hist_opti, cash_plan=context.opti_cash_plan)  # 在生成交易信号之前准备历史数据
        pars, perfs = 0, 0
        # TODO: 重构这段代码，使用运行模式字典代替一连串的if判断
        if how == 0:
            """ Exhausetive Search 穷举法
            
                穷举法是最简单和直接的参数优化方法，在已经定义好的参数空间中，按照一定的间隔均匀地从向量空间中取出一系列的点，逐个在优化空间
                中生成交易信号并进行回测，把所有的参数组合都测试完毕后，根据目标函数的值选择排名靠前的参数组合即可。
                
                穷举法能确保找到参数空间中的全剧最优参数，不过必须逐一测试所有可能的参数点，因此计算量相当大。同时，穷举法只适用于非连续的参数
                空间，对于连续空间，仍然可以使用穷举法，但无法真正"穷尽"所有的参数组合
                
                关于穷举法的具体参数和输出，参见self._search_exhaustive()函数的docstring
            """
            pars, perfs = _search_exhaustive(hist=hist_opti,
                                             ref=hist_reference,
                                             op=operator,
                                             context=context)
        elif how == 1:
            """ Montecarlo蒙特卡洛方法
            
                蒙特卡洛法与穷举法类似，也需要检查并测试参数空间中的大量参数组合。不过在蒙特卡洛法中，参数组合是从参数空间中随机选出的，而且在
                参数空间中均匀分布。与穷举法相比，蒙特卡洛方法更适合于连续参数空间。
                
                关于蒙特卡洛方法的参数和输出，参见self._search_montecarlo()函数的docstring
            """
            pars, perfs = _search_montecarlo(hist=hist_opti,
                                             ref=hist_reference,
                                             op=operator,
                                             context=context)
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
            pars, perfs = _search_incremental(hist=hist_opti,
                                              ref=hist_reference,
                                              op=operator,
                                              context=context)
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

        print(f'====================================\n'
              f'|                                  |\n'
              f'|       OPTIMIZATION RESULT        |\n'
              f'|                                  |\n'
              f'====================================\n')
        print(f'Searching finished, {len(perfs)} best results are generated')
        print(f'The best parameter performs {perfs[-1]/perfs[0]:.3f} times better than the least performing result')
        print(f'best result: {perfs[-1]:.3f} obtained at parameter: \n{pars[-1]}')
        print(f'least result: {perfs[0]:.3f} obtained at parameter: \n{pars[0]}')
        print(f'==========VALIDATION OF OPTIMIZATION RESULTS============')
        # TODO: 在返回优化的pars/perfs之前，应该先将所有的pars在测试区间上进行
        # TODO: 测试，并将打印/输出测试评价指标的统计结果。
        test_result_df = pd.DataFrame(columns=['par',
                                               'sell_count',
                                               'buy_count',
                                               'oper_count',
                                               'total_fee',
                                               'final_value',
                                               'total_return',
                                               'annual_return',
                                               'mdd',
                                               'volatility',
                                               'alpha',
                                               'beta',
                                               'sharp',
                                               'info'])
        operator.prepare_data(hist_data=hist_test, cash_plan=context.test_cash_plan)
        for par in pars:
            operator.set_opt_par(par)  # 设置需要优化的策略参数
            op_list = operator.create_signal(hist_test)
            looped_values = apply_loop(op_list=op_list,
                                       history_list=hist_test_loop,
                                       cash_plan=context.test_cash_plan,
                                       cost_rate=context.rate,
                                       moq=context.moq)
            years, oper_count, total_invest, total_fee = _eval_operation(op_list=op_list,
                                                                         looped_value=looped_values,
                                                                         cash_plan=context.test_cash_plan)
            # 评价回测结果——计算回测终值
            final_value = _eval_fv(looped_val=looped_values)
            # 评价回测结果——计算总投资收益率
            ret = final_value / total_invest
            # 评价回测结果——计算最大回撤比例以及最大回撤发生日期
            mdd, max_date, low_date = _eval_max_drawdown(looped_values)
            # 评价回测结果——计算投资期间的波动率系数
            volatility = _eval_volatility(looped_values)
            # 评价回测结果——计算投资期间的beta贝塔系数
            beta = _eval_beta(looped_values, hist_reference, reference_data)
            # 评价回测结果——计算投资期间的夏普率
            sharp = _eval_sharp(looped_values, total_invest, 0.015)
            # 评价回测结果——计算投资期间的alpha阿尔法系数
            alpha = _eval_alpha(looped_values, total_invest, hist_reference, reference_data)
            # 评价回测结果——计算投资回报的信息比率
            info = _eval_info_ratio(looped_values, hist_reference, reference_data)
            # debug
            # print(f'tested parameter {par} on period: {looped_values.index[0]} to {looped_values.index[-1]} and got:\n'
            #       f'total final values: {final_value}, other performance indicators are:\n')
            # print({'par'            :par,
            #        'sell_count'     :oper_count.sell.sum(),
            #        'buy_count'      :oper_count.buy.sum(),
            #        'oper_count'     :oper_count.total.sum(),
            #        'total_fee'      :total_fee,
            #        'final_value'    :final_value,
            #        'total_return'   :ret - 1,
            #        'annual_return'  :ret ** (1 / years) - 1,
            #        'mdd'   :mdd,
            #        'volatility'     :volatility,
            #        'alpha'          :alpha,
            #        'beta'           :beta,
            #        'sharp'          :sharp,
            #        'info'           :info})
            test_result_df = test_result_df.append({'par'            :par,
                                                    'sell_count'     :oper_count.sell.sum(),
                                                    'buy_count'      :oper_count.buy.sum(),
                                                    'oper_count'     :oper_count.total.sum(),
                                                    'total_fee'      :total_fee,
                                                    'final_value'    :final_value,
                                                    'total_return'   :ret - 1,
                                                    'annual_return'  :ret ** (1 / years) - 1,
                                                    'mdd'   :mdd,
                                                    'volatility'     :volatility,
                                                    'alpha'          :alpha,
                                                    'beta'           :beta,
                                                    'sharp'          :sharp,
                                                    'info'           :info
                                                    },
                                                   ignore_index=True)

        # 评价回测结果——计算参考数据收益率以及平均年化收益率
        ref_rtn, ref_annual_rtn = _eval_benchmark(looped_values, hist_reference, reference_data)
        print(f'investment starts on {looped_values.index[0]}\nends on {looped_values.index[-1]}\n'
              f'Total looped periods: {years} years.')
        print(f'total investment amount: ¥{total_invest:13,.2f}')
        print(f'Reference index type is {context.reference_asset} at {context.reference_asset_type}\n'
              f'Total reference return: {ref_rtn * 100:.3f}% \n'
              f'Average Yearly reference return rate: {ref_annual_rtn * 100:.3f}%')
        print(f'statistical analysis of optimal strategy performance indicators: \n'
              f'annual return:       {test_result_df.annual_return.mean() * 100:.3f}% ±'
              f' {test_result_df.annual_return.std() * 100:.3f}%\n'
              f'alpha:               {test_result_df.alpha.mean():.3f} ± {test_result_df.alpha.std():.3f}\n'
              f'Beta:                {test_result_df.beta.mean():.3f} ± {test_result_df.beta.std():.3f}\n'
              f'Sharp ratio:         {test_result_df.sharp.mean():.3f} ± {test_result_df.sharp.std():.3f}\n'
              f'Info ratio:          {test_result_df["info"].mean():.3f} ± {test_result_df["info"].std():.3f}\n'
              f'250 day volatility:  {test_result_df.volatility.mean():.3f} ± {test_result_df.volatility.std():.3f}\n'
              f'other performance indicators are listed in below table\n')
        print(test_result_df[["par","sell_count", "buy_count", "oper_count", "total_fee",
                              "final_value", "total_return", "mdd"]])
        print(f'\n===========END OF REPORT=============\n')
        return perfs, pars
    elif run_mode == 3:
        """ 进入策略统计预测分析模式
        
        使用蒙特卡洛方法预测策略的未来表现。
        
        """
        print(f'====================================\n'
              f'|                                  |\n'
              f'|       PREDICTIVE RESULTS         |\n'
              f'|                                  |\n'
              f'====================================\n')
        raise NotImplementedError


def _get_parameter_performance(par: tuple,
                               op: Operator,
                               hist: HistoryPanel,
                               history_list: pd.DataFrame,
                               context: Context) -> float:
    """ 所有优化函数的核心部分，将par传入op中，并给出一个float，代表这组参数的表现评分值performance

    input:
        :param par:  tuple: 一组参数，包含多个策略的参数的混合体
        :param op:  Operator: 一个operator对象，包含多个投资策略
        :param hist:  用于生成operation List的历史数据
        :param history_list: 用于进行回测的历史数据
        :param context: 上下文对象，用于保存相关配置
    :return:
        float 一个代表该策略在使用par作为参数时的性能表现评分
    """
    op.set_opt_par(par)  # 设置需要优化的策略参数
    # 生成交易清单并进行模拟交易生成交易记录
    op_list = op.create_signal(hist)
    if op_list.empty:  # 如果策略无法产生有意义的操作清单，则直接返回0
        return 0
    looped_val = apply_loop(op_list=op_list,
                            history_list=history_list,
                            cash_plan=context.cash_plan,
                            cost_rate=context.rate,
                            moq=context.moq)
    # 使用评价函数计算该组参数模拟交易的评价值
    perf = _eval_fv(looped_val)
    return perf


# TODO: refactor this segment of codes: merge all _search_XXX() functions into a simpler way
def _search_exhaustive(hist, ref, op, context):
    """ 最优参数搜索算法1: 穷举法或间隔搜索法

        逐个遍历整个参数空间（仅当空间为离散空间时）的所有点并逐一测试，或者使用某个固定的
        “间隔”从空间中逐个取出所有的点（不管离散空间还是连续空间均适用）并逐一测试，
        寻找使得评价函数的值最大的一组或多组参数

    input:
        :param hist，object，历史数据，优化器的整个优化过程在历史数据上完成
        :param op，object，交易信号生成器对象
        :param context, object, 用于存储优化参数的上下文对象
    return: =====tuple对象，包含两个变量
        pars 作为结果输出的参数组
        perfs 输出的参数组的评价分数
    """
    pool = ResultPool(context.output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.opt_space_par
    space = Space(s_range, s_type)  # 生成参数空间

    # 使用extract从参数空间中提取所有的点，并打包为iterator对象进行循环
    i = 0
    it, total = space.extract(context.opti_method_step_size)
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
    best_so_far = 0
    if context.parallel:
        # 启用并行计算
        proc_pool = ProcessPoolExecutor()
        futures = {proc_pool.submit(_get_parameter_performance, par, op, hist, history_list, context): par for par in
                   it}
        for f in as_completed(futures):
            pool.in_pool(futures[f], f.result())
            i += 1
            if f.result() > best_so_far:
                best_so_far = f.result()
            if i % 10 == 0:
                progress_bar(i, total, comments=f'best performance: {best_so_far:.3f}')
    else:
        for par in it:
            perf = _get_parameter_performance(par=par, op=op, hist=hist, history_list=history_list, context=context)
            pool.in_pool(par, perf)
            i += 1
            if perf > best_so_far:
                best_so_far = perf
            if i % 10 == 0:
                progress_bar(i, total, comments=f'best performance: {best_so_far:.3f}')
    # 将当前参数以及评价结果成对压入参数池中，并去掉最差的结果
    # 至于去掉的是评价函数最大值还是最小值，由keep_largest_perf参数确定
    # keep_largest_perf为True则去掉perf最小的参数组合，否则去掉最大的组合
    progress_bar(i, i)
    pool.cut(context.larger_is_better)
    et = time.time()
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st)}')
    return pool.pars, pool.perfs


def _search_montecarlo(hist, ref, op, context):
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
    pool = ResultPool(context.output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.opt_space_par
    space = Space(s_range, s_type)  # 生成参数空间
    # 使用随机方法从参数空间中取出point_count个点，并打包为iterator对象，后面的操作与穷举法一致
    i = 0
    it, total = space.extract(context.opti_method_sample_size, how='rand')
    # debug
    # print('Result pool has been created, capacity of result pool: ', pool.capacity)
    # print('Searching Space has been created: ')
    # space.info()
    # print('Number of points to be checked:', total)
    # print('Searching Starts...')
    history_list = hist.to_dataframe(htype='close').fillna(0)
    st = time.time()
    best_so_far = 0
    if context.parallel:
        # 启用并行计算
        proc_pool = ProcessPoolExecutor()
        futures = {proc_pool.submit(_get_parameter_performance, par, op, hist, history_list, context): par for par in
                   it}
        for f in as_completed(futures):
            pool.in_pool(futures[f], f.result())
            i += 1
            if f.result() > best_so_far:
                best_so_far = f.result()
            if i % 10 == 0:
                progress_bar(i, total, comments=f'best performance: {best_so_far:.3f}')
    else:
        # 禁用并行计算
        for par in it:
            perf = _get_parameter_performance(par=par, op=op, hist=hist, history_list=history_list, context=context)
            pool.in_pool(par, perf)
            i += 1
            if perf > best_so_far:
                best_so_far = perf
            if i % 10 == 0:
                progress_bar(i, total, comments=f'best performance: {best_so_far:.3f}')
    pool.cut(context.maximize_result)
    et = time.time()
    progress_bar(total, total)
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st, short_form=True)}')
    return pool.pars, pool.perfs


def _search_incremental(hist, ref, op, context):
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
    init_step = context.opti_method_init_step_size
    min_step = context.opti_method_min_step_size
    inc_step = context.opti_method_incre_ratio
    parallel = context.parallel
    pool = ResultPool(context.output_count)  # 用于存储中间结果或最终结果的参数池对象
    s_range, s_type = op.opt_space_par
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
                proc_pool = ProcessPoolExecutor()
                futures = {proc_pool.submit(_get_parameter_performance, par, op, hist,
                                            history_list, context): par for
                           par in it}
                for f in as_completed(futures):
                    pool.in_pool(futures[f], f.result())
                    i += 1
                    if i % 10 == 0:
                        progress_bar(i, total_calc_rounds, f'step size: {step_size}')
            else:
                # 禁用并行计算
                for par in it:
                    # 以下所有函数都是循环内函数，需要进行提速优化
                    # 以下所有函数在几种优化算法中是相同的，因此可以考虑简化
                    perf = _get_parameter_performance(par=par, op=op, hist=hist, history_list=history_list,
                                                      context=context)
                    pool.in_pool(par, perf)
                    i += 1
                    if i % 20 == 0:
                        progress_bar(i, total_calc_rounds, f'step size: {step_size}')
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
        progress_bar(i, total_calc_rounds, f'step size: {step_size}')
    et = time.time()
    progress_bar(i, i, f'step size: {step_size}')
    print(f'\nOptimization completed, total time consumption: {time_str_format(et - st)}')
    return pool.pars, pool.perfs


def _search_ga(hist, ref, op, context):
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


def _get_yearly_span(value_df: pd.DataFrame) -> float:
    """ 计算回测结果的时间跨度，单位为年。一年按照365天计算

    :param value_df: pd.DataFrame, 回测结果
    :return:
    """
    if not isinstance(value_df, pd.DataFrame):
        raise TypeError(f'Looped value should be a pandas DataFrame, got {type(value_df)} instead!')
    first_day = value_df.index[0]
    last_day = value_df.index[-1]
    if isinstance(last_day, (int, float)) and isinstance(first_day, (int, float)):
        total_year = (last_day - first_day) / 365.
    else:
        try:
            total_year = (last_day - first_day).days / 365.
        except:
            raise ValueError(f'The yearly time span of the looped value can not be calculated, '
                             f'DataFrame index should be time or number format!, '
                             f'got {type(first_day)} and {type(last_day)}')
    return total_year


def _eval_benchmark(looped_value, reference_value, reference_data):
    """ 参考标准年化收益率。具体计算方式为 （(参考标准最终指数 / 参考标准初始指数) ** 1 / 回测交易年数 - 1）

        :param looped_value:
        :param reference_value:
        :param reference_data:
        :return:
    """
    total_year = _get_yearly_span(looped_value)

    rtn_data = reference_value[reference_data]
    rtn = (rtn_data[looped_value.index[-1]] / rtn_data[looped_value.index[0]])
    # # debug
    # print(f'total year is \n{total_year}')
    # print(f'total return is: \n{rtn_data[looped_value.index[-1]]} / {rtn_data[looped_value.index[0]]} = \n{rtn - 1}')
    # print(f'yearly return is:\n{rtn ** (1/total_year) - 1}')
    return rtn - 1, rtn ** (1 / total_year) - 1.


def _eval_alpha(looped_value, total_invest, reference_value, reference_data, risk_free_ror: float = 0.035):
    """ 回测结果评价函数：alpha率

    阿尔法。具体计算方式为 (策略年化收益 - 无风险收益) - b × (参考标准年化收益 - 无风险收益)，
    这里的无风险收益指的是中国固定利率国债收益率曲线上10年期国债的年化到期收益率。
    :param looped_value:
    :param total_invest:
    :param reference_value:
    :param reference_data:
    :return:
    """
    total_year = _get_yearly_span(looped_value)
    final_value = _eval_fv(looped_value)
    strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
    reference_return, reference_yearly_return = _eval_benchmark(looped_value, reference_value, reference_data)
    b = _eval_beta(looped_value, reference_value, reference_data)
    return (strategy_return - risk_free_ror) - b * (reference_yearly_return - risk_free_ror)


def _eval_beta(looped_value, reference_value, reference_data):
    """ 贝塔。具体计算方法为 策略每日收益与参考标准每日收益的协方差 / 参考标准每日收益的方差 。

    :param looped_value: pandas.DataFrame, 回测结果，需要计算Beta的股票价格或投资收益历史价格
    :param reference_value: pandas.DataFrame, 参考结果，用于评价股票价格波动的基准价格，通常用市场平均或股票指数价格代表，代表市场平均波动
    :param reference_data: str: 参考结果的数据类型，如close, open, low 等
    :return:
    """
    if not isinstance(reference_value, pd.DataFrame):
        raise TypeError(f'reference value should be pandas DataFrame, got {type(reference_value)} instead!')
    if not isinstance(looped_value, pd.DataFrame):
        raise TypeError(f'looped value should be pandas DataFrame, got {type(looped_value)} instead')
    if not reference_data in reference_value.columns:
        raise KeyError(f'reference data should \'{reference_data}\' can not be found in reference data')
    ret = (looped_value['value'] / looped_value['value'].shift(1)) - 1
    ret_dev = ret.var()
    ref = reference_value[reference_data]
    ref_ret = (ref / ref.shift(1)) - 1
    looped_value['ref'] = ref_ret
    looped_value['ret'] = ret
    # debug
    # print(f'return is:\n{looped_value.ret.values}')
    # print(f'reference value is:\n{looped_value.ref.values}')
    return looped_value.ref.cov(looped_value.ret) / ret_dev


def _eval_sharp(looped_value, total_invest, riskfree_interest_rate: float = 0.035):
    """ 夏普比率。表示每承受一单位总风险，会产生多少的超额报酬。

    具体计算方法为 (策略年化收益率 - 回测起始交易日的无风险利率) / 策略收益波动率 。

    :param looped_value:
    :return:
    """
    total_year = _get_yearly_span(looped_value)
    final_value = _eval_fv(looped_value)
    strategy_return = (final_value / total_invest) ** (1 / total_year) - 1
    volatility = _eval_volatility(looped_value, logarithm=False)
    # debug
    # print(f'yearly return is: \n{final_value} / {total_invest} = \n{strategy_return}\n'
    #       f'volatility is:  \n{volatility}')
    return (strategy_return - riskfree_interest_rate) / volatility


def _eval_volatility(looped_value, logarithm: bool = True):
    """ 策略收益波动率。用来测量资产的风险性。具体计算方法为 策略每日收益的年化标准差。可以使用logarithm参数指定是否计算对数收益率

    :param looped_value:
    :parma logarithm: 是否计算指数收益率，默认为True，计算对数收益率，为False时计算常规收益率
    :return:
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if not looped_value.empty:
        if logarithm:
            ret = np.log(looped_value['value'] / looped_value['value'].shift(1))
        else:
            ret = (looped_value['value'] / looped_value['value'].shift(1)) - 1
        # debug
        # looped_value['ret'] = ret
        # print(f'return is \n {looped_value}')
        if len(ret) > 250:
            volatility = ret.rolling(250).std() * np.sqrt(250)
            # debug
            # print(f'standard deviations (a list rolling calculated) are {ret.rolling(250).std()}')
            return volatility.iloc[-1]
        else:
            volatility = ret.std() * np.sqrt(250)
            # debug
            # print(f'standard deviation (a single number with all data) is {ret.std()}')
            return volatility
    else:
        return -np.inf


def _eval_info_ratio(looped_value, reference_value, reference_data):
    """ 信息比率。衡量超额风险带来的超额收益。具体计算方法为 (策略每日收益 - 参考标准每日收益)的年化均值 / 年化标准差 。
        information ratio = (portfolio return - reference return) / tracking error

    :param looped_value:
    :return:
    """
    ret = (looped_value['value'] / looped_value['value'].shift(1)) - 1
    ref = reference_value[reference_data]
    ref_ret = (ref / ref.shift(1)) - 1
    track_error = (ref_ret - ret).std(
            ddof=0)  # set ddof=0 to calculate population standard deviation, or 1 for sample deviation
    # debug
    # print(f'average return is {ret.mean()} from:\n{ret}\n'
    #       f'average reference return is {ref_ret.mean()} from: \n{ref_ret}\n'
    #       f'tracking error is {track_error} from difference of return:\n{ref_ret - ret}')
    return (ret.mean() - ref_ret.mean()) / track_error


def _eval_max_drawdown(looped_value):
    """ 最大回撤。描述策略可能出现的最糟糕的情况。具体计算方法为 max(1 - 策略当日价值 / 当日之前虚拟账户最高价值)

    :param looped_value:
    :return:
    """
    assert isinstance(looped_value, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_value)} instead'
    if not looped_value.empty:
        max_val = 0.
        drawdown = 0.
        max_drawdown = 0.
        current_max_date = 0.
        max_value_date = 0.
        max_drawdown_date = 0.
        for date, value in looped_value.value.iteritems():
            if value > max_val:
                max_val = value
                current_max_date = date
            if max_val != 0:
                drawdown = 1 - value / max_val
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_date = date
                max_value_date = current_max_date
        return max_drawdown, max_value_date, max_drawdown_date
    else:
        return -np.inf


def _eval_fv(looped_val):
    """评价函数 Future Value 终值评价

    '投资模拟期最后一个交易日的资产总值

    input:
        :param looped_val，ndarray，回测器生成输出的交易模拟记录
    return:
        perf: float，应用该评价方法对回测模拟结果的评价分数

"""
    assert isinstance(looped_val, pd.DataFrame), \
        f'TypeError, looped value should be pandas DataFrame, got {type(looped_val)} instead'
    # debug
    # print(f'======================================\n'
    #       f'=                                    =\n'
    #       f'=   Start Evaluation of final value  =\n'
    #       f'=                                    =\n'
    #       f'======================================\n'
    #       f'IN EVAL_FV:\n'
    #       f'got DataFrame as following: \n{looped_val.info()}')
    if not looped_val.empty:
        try:
            perf = looped_val['value'].iloc[-1]
            return perf
        except:
            raise KeyError(f'the key \'value\' can not be found in given looped value!')
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