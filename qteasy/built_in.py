# coding=utf-8
# build_in.py

# ======================================
# This file contains concrete strategy
# classes that are inherited form
# strategy.Strategy class and its sub
# classes like strategy.RollingTiming
# etc.
# ======================================

import numpy as np
import qteasy.strategy as stg
from .tafuncs import sma, ema, trix, cdldoji, bbands


# All following strategies can be used to create strategies by referring to its name
# Built-in Rolling timing strategies:

class TestTimingClass(stg.RollingTiming):
    """Test strategy that uses abstract class from another file
    """
    def __init__(self):
        """

        """
        super().__init__()
        pass

    def _realize(self, hist_data, params):
        print(f'test strategy with imported abc done!\n'
              f'got parameters: {params}\n'
              f'got hist data shaped: {hist_data.shape}')


class TimingCrossline(stg.RollingTiming):
    """crossline择时策略类，利用长短均线的交叉确定多空状态

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用4个参数，
        s: int, 短均线计算日期；
        l: int, 长均线计算日期；
        m: int, 均线边界宽度；
        hesitate: str, 均线跨越类型
    参数输入数据范围：[(10, 250), (10, 250), (10, 250), ('buy', 'sell', 'none')]

    """

    def __init__(self, pars: tuple = None):
        """Crossline交叉线策略只有一个动态属性，其余属性均不可变"""
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['discr', 'discr', 'conti', 'enum'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (1, 100), ('buy', 'sell', 'none')],
                         stg_name='CROSSLINE STRATEGY',
                         stg_text='Moving average crossline strategy, determine long/short position according to the ' \
                                  'cross point of long and short term moving average prices ',
                         data_types='close')

    def _realize(self, hist_data, params):
        """crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        s, l, m, hesitate = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        # 计算长短均线之间的距离
        diff = (sma(h[0], l) - sma(h[0], s))[-1]
        # 根据观望模式在不同的点位产生Long/short标记
        if hesitate == 'buy':
            m = -m
        elif hesitate == 'sell':
            pass
        else:  # hesitate == 'none'
            m = 0
        if diff < m:
            return 1
        else:
            return 0


class TimingMACD(stg.RollingTiming):
    """MACD择时策略类，运用MACD均线策略，在hist_price Series对象上生成交易信号

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用3个参数，
        s: int,
        l: int,
        d: int,
    参数输入数据范围：[(10, 250), (10, 250), (10, 250)]
    """

    def __init__(self, pars: tuple = None):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (10, 250)],
                         stg_name='MACD STRATEGY',
                         stg_text='MACD strategy, determin long/short position according to differences of '
                                  'exponential weighted moving average prices',
                         data_types='close')

    def _realize(self, hist_data, params):
        """生成单只个股的择时多空信号
        生成MACD多空判断：
        1， MACD柱状线为正，多头状态，为负空头状态：由于MACD = diff - dea

        输入:
            idx: 指定的参考指数历史数据
            sRange, 短均线参数，短均线的指数移动平均计算窗口宽度，单位为日
            lRange, 长均线参数，长均线的指数移动平均计算窗口宽度，单位为日
            dRange, DIFF的指数移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """

        s, l, m = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T

        # 计算指数的指数移动平均价格
        diff = ema(h[0], s) - ema(h[0], l)
        dea = ema(diff, m)
        _macd = 2 * (diff - dea)
        # 以下使用utfuncs中的macd函数（基于talib）生成相同结果，但速度稍慢
        # diff, dea, _macd = macd(hist_data, s, l, m)


        if _macd[-1] > 0:
            return 1
        else:
            return 0


class TimingDMA(stg.RollingTiming):
    """DMA择时策略
    生成DMA多空判断：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        3， DMA与股价发生背离时的交叉信号，可信度较高

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用3个参数，
        s: int,
        l: int,
        d: int,
    参数输入数据范围：[(10, 250), (10, 250), (10, 250)]
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (10, 250)],
                         stg_name='DMA STRATEGY',
                         stg_text='DMA strategy, determin long/short position according to differences of moving '
                                  'average prices',
                         data_types='close')

    def _realize(self, hist_data, params):
        # 使用基于np的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        # print 'Generating Quick dma Long short Mask with parameters', params

        # 计算指数的移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        dma = sma(h[0], s) - sma(h[0], l)
        ama = dma.copy()
        ama[~np.isnan(dma)] = sma(dma[~np.isnan(dma)], d)
        # print('qDMA generated DMA and ama signal:', dma.size, dma, '\n', ama.size, ama)

        if dma[-1] > ama[-1]:
            return 1
        else:
            return 0


class TimingTRIX(stg.RollingTiming):
    """TRIX择时策略，运用TRIX均线策略，利用历史序列上生成交易信号

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270天
    策略使用2个参数，
        s: int, 短均线参数，短均线的移动平均计算窗口宽度，单位为日
        m: int, DIFF的移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”
    参数输入数据范围：[(10, 250), (10, 250)]
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'discr'],
                         par_bounds_or_enums=[(2, 50), (3, 150)],
                         stg_name='TRIX STRATEGY',
                         stg_text='TRIX strategy, determine long/short position according to triple exponential '
                                  'weighted moving average prices',
                         data_freq='d',
                         sample_freq='d',
                         window_length=270,
                         data_types='close')

    def _realize(self, hist_data, params):
        """参数:

        input:
        :param hist_data:
        :param params:
        :return:

        """
        s, m = params
        # print 'Generating trxi Long short Mask with parameters', params

        # 计算指数的指数移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        trx = trix(h[0], s) * 100
        # debug
        # print(f'In TimingTRIX strategy calculated with s = {s} and input data:\n{np.round(h[0], 3)} \n'
        #       f'triple ema: \n{np.round(trx, 3)}')
        matrix = sma(trx, m)
        # debug:
        # print(f'In TimingTRIX strategy calculated matrix with m = {m} is:\n{np.round(matrix, 3)}')

        # 生成TRIX多空判断：
        # 1， TRIX位于MATRIX上方时，长期多头状态, signal = 1
        # 2， TRIX位于MATRIX下方时，长期空头状态, signal = 0
        if trx[-1] > matrix[-1]:
            return 1
        else:
            return 0


class TimingBBand(stg.SimpleTiming):
    """BBand择时策略，运用布林带线策略，利用历史序列上生成交易信号

        数据类型：close 收盘价，单数据输入
        数据分析频率：天
        数据窗口长度：270天
        策略使用2个参数，
            span: int, 移动平均计算窗口宽度，单位为日
            upper: float, 布林带的上边缘所处的标准差倍数
            lower: float, 布林带的下边缘所处的标准差倍数
        参数输入数据范围：[(10, 250), (0.5, 2.5), (0.5, 2.5)]
        """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'conti', 'conti'],
                         par_bounds_or_enums=[(10, 250), (0.5, 2.5), (0.5, 2.5)],
                         stg_name='BBand STRATEGY',
                         stg_text='BBand strategy, determine long/short position according to Bollinger bands',
                         data_freq='d',
                         sample_freq='d',
                         window_length=270,
                         data_types=['close', 'high', 'low'])

    def _realize(self, hist_data, params):

        span, upper, lower = params
        # 计算指数的指数移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        avg_price = np.mean(h[0], 1)
        upper, middle, lower = bbands(close=avg_price, timeperiod=span, nbdevup=upper, nbdevdn=lower)

        # 生成BBANDS操作信号判断：
        # 1, 当avg_price从上至下穿过布林带上缘时，产生空头建仓或平多仓信号 -1
        # 2, 当avg_price从下至上穿过布林带下缘时，产生多头建仓或平空仓信号 +1
        # 3, 其余时刻不产生任何信号
        if avg_price[-2] >= upper[-2] and avg_price[-1] < upper[-1]:
            return -1
        elif avg_price[-2] <= lower[-2] and avg_price[-1] > lower[-1]:
            return +1
        else:
            return 0


class TimingCDL(stg.RollingTiming):
    """CDL择时策略，在K线图中找到符合要求的cdldoji模式

    数据类型：open, high, low, close 开盘，最高，最低，收盘价，多数据输入
    数据分析频率：天
    数据窗口长度：100天
    参数数量：0个，参数类型：N/A，输入数据范围：N/A
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=0,
                         par_types=None,
                         par_bounds_or_enums=None,
                         stg_name='CDL INDICATOR STRATEGY',
                         stg_text='CDL Indicators, determine long/short position according to CDL Indicators',
                         window_length=200,
                         data_types='open,high,low,close')

    def _realize(self, hist_data, params=None):
        """参数:

        input:
            None
        """
        # 计算历史数据上的CDL指标
        h = hist_data.T
        cat = (cdldoji(h[0], h[1], h[2], h[3]).cumsum() // 100)

        return float(cat[-1])

# Built in Simple timing strategies:

class RiconNone(stg.SimpleTiming):
    """无风险控制策略，不对任何风险进行控制"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='NONE',
                         stg_text='Do not take any risk control activity')

    def _realize(self, hist_data, params=None):
        return np.zeros_like(hist_data.squeeze())


class TimingLong(stg.SimpleTiming):
    """简单择时策略，返回整个历史周期上的恒定多头状态

    数据类型：N/A
    数据分析频率：N/A
    数据窗口长度：N/A
    策略使用0个参数，
    参数输入数据范围：N/A
    """

    def __init__(self):
        super().__init__(stg_name='Long',
                         stg_text='Simple Timing strategy, return constant long position on the whole history')

    def _realize(self, hist_data, params):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return np.ones_like(hist_data.squeeze())


class TimingShort(stg.SimpleTiming):
    """简单择时策略，返回整个历史周期上的恒定空头状态

    数据类型：N/A
    数据分析频率：N/A
    数据窗口长度：N/A
    策略使用0个参数，
    参数输入数据范围：N/A
    """

    def __init__(self):
        super().__init__(stg_name='Short',
                         stg_text='Simple Timing strategy, return constant Short position on the whole history')

    def _realize(self, hist_data, params):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return -np.ones_like(hist_data.squeeze())


class TimingZero(stg.SimpleTiming):
    """简单择时策略，返回整个历史周期上的空仓状态

    数据类型：N/A
    数据分析频率：N/A
    数据窗口长度：N/A
    策略使用0个参数，
    参数输入数据范围：N/A
    """

    def __init__(self):
        super().__init__(stg_name='Zero',
                         stg_text='Simple Timing strategy, return constant Zero position ratio on the whole history')

    def _realize(self, hist_data, params):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return np.zeros_like(hist_data.squeeze())


class SimpleDMA(stg.SimpleTiming):
    """DMA择时策略
    生成DMA多空判断：
        1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        3， DMA与股价发生背离时的交叉信号，可信度较高

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270
    策略使用3个参数，
        s: int,
        l: int,
        d: int,
    参数输入数据范围：[(10, 250), (10, 250), (10, 250)]
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=3,
                         par_types=['discr', 'discr', 'discr'],
                         par_bounds_or_enums=[(10, 250), (10, 250), (10, 250)],
                         stg_name='QUICK DMA STRATEGY',
                         stg_text='Quick DMA strategy, determine long/short position according to differences of '
                                  'moving average prices with simple timing strategy',
                         data_types='close')

    def _realize(self, hist_data, params):
        # 使用基于np的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        # print 'Generating Quick dma Long short Mask with parameters', params

        # 计算指数的移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_data.T
        dma = sma(h[0], s) - sma(h[0], l)
        ama = dma.copy()
        ama[~np.isnan(dma)] = sma(dma[~np.isnan(dma)], d)
        # print('qDMA generated DMA and ama signal:', dma.size, dma, '\n', ama.size, ama)

        cat = np.where(dma > ama, 1, 0)
        return cat


class RiconUrgent(stg.SimpleTiming):
    """urgent风控类，继承自Ricon类，重写_realize方法"""

    # 跌幅控制策略，当N日跌幅超过p%的时候，强制生成卖出信号

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=2,
                         par_types=['discr', 'conti'],
                         par_bounds_or_enums=[(1, 40), (-0.5, 0.5)],
                         stg_name='URGENT',
                         stg_text='Generate selling signal when N-day drop rate reaches target')

    def _realize(self, hist_data, params):
        """
        # 根据N日内下跌百分比确定的卖出信号，让N日内下跌百分比达到pct时产生卖出信号

        input =====
            :type hist_data: tuple like (N, pct): type N: int, Type pct: float
                输入参数对，当股价在N天内下跌百分比达到pct时，产生卖出信号
        return ====
            :rtype: object np.ndarray: 包含紧急卖出信号的ndarray
        """
        assert self._pars is not None, 'Parameter of Risk Control-Urgent should be a pair of numbers like (N, ' \
                                       'pct)\nN as days, pct as percent drop '
        assert isinstance(hist_data, np.ndarray), \
            f'Type Error: input historical data should be ndarray, got {type(hist_data)}'
        # debug
        # print(f'hist data: \n{hist_data}')
        day, drop = self._pars
        h = hist_data
        diff = (h - np.roll(h, day)) / h
        diff[:day] = h[:day]
        # debug
        # print(f'input array got in Ricon.generate() is shaped {hist_data.shape}')
        # print(f'and the hist_data is converted to shape {h.shape}')
        # print(f'diff result:\n{diff}')
        # print(f'created array in ricon generate() is shaped {diff.shape}')
        # print(f'created array in ricon generate() is {np.where(diff < drop)}')
        return np.where(diff < drop, -1, 0).squeeze()


# Built in Selecting strategies:

class SelectingSimple(stg.Selecting):
    """基础选股策略：保持历史股票池中的所有股票都被选中，投资比例平均分配"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='SIMPLE SELECTING',
                         stg_text='Selecting all share and distribute weights evenly')

    def _realize(self, hist_data):
        # 所有股票全部被选中，投资比例平均分配
        share_count = hist_data.shape[0]
        return [1. / share_count] * share_count


class SelectingRandom(stg.Selecting):
    """基础选股策略：在每个历史分段中，按照指定的概率（p<1时）随机抽取若干股票，或随机抽取指定数量（p>1）的股票进入投资组合，投资比例平均分配"""

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         stg_name='RANDOM SELECTING',
                         stg_text='Selecting share Randomly and distribute weights evenly')

    def _realize(self, hist_data):
        pct = self.pars[0]
        share_count = hist_data.shape[0]
        if pct < 1:
            # 给定参数小于1，按照概率随机抽取若干股票
            chosen = np.random.choice([1, 0], size=share_count, p=[pct, 1 - pct])
        else:  # pct >= 1 给定参数大于1，抽取给定数量的股票
            choose_at = np.random.choice(share_count, size=(int(pct)), replace=False)
            chosen = np.zeros(share_count)
            chosen[choose_at] = 1
        return chosen.astype('float') / chosen.sum()  # 投资比例平均分配


class SelectingFinance(stg.Selecting):
    """ 根据所有股票的上期财报或过去多期财报中的某个指标选股，按照指标数值分配选股权重

        数据类型：由data_types指定的财报指标财报数据，单数据输入，默认数据为EPS
        数据分析频率：季度
        数据窗口长度：90
        策略使用3个参数:
            largest_win:    bool,   为真时选出EPS最高的股票，否则选出EPS最低的股票
            distribution:   str ,   确定如何分配选中股票的权重,
            drop_threshold: float,  确定丢弃值，丢弃当期EPS低于该值的股票
            pct:            float,  确定从股票池中选出的投资组合的数量或比例，当0<pct<1时，选出pct%的股票，当pct>=1时，选出pct只股票
        参数输入数据范围：[(True, False), ('even', 'linear', 'proportion'), (0, 100)]
    """

    def __init__(self, pars=None):
        super().__init__(pars=pars,
                         par_count=4,
                         par_types=['enum', 'enum', 'discr', 'conti'],
                         par_bounds_or_enums=[(True, False), ('even', 'linear', 'proportion'), (0, 100), (0, 1)],
                         stg_name='FINANCE SELECTING',
                         stg_text='Selecting share_pool according to financial report EPS indicator',
                         data_freq='d',
                         sample_freq='y',
                         window_length=90,
                         data_types='eps')

    # TODO: 因为Strategy主类代码重构，ranking table的代码结构也应该相应修改，待修改
    def _realize(self, hist_data):
        """ 根据hist_segment中的EPS数据选择一定数量的股票

        """
        largest_win, distribution, drop_threshold, pct = self.pars
        share_count = hist_data.shape[0]
        if pct < 1:
            # pct 参数小于1时，代表目标投资组合在所有投资产品中所占的比例，如0.5代表需要选中50%的投资产品
            pct = int(share_count * pct)
        else:  # pct 参数大于1时，取整后代表目标投资组合中投资产品的数量，如5代表需要选中5只投资产品
            pct = int(pct)
        # 历史数据片段必须是ndarray对象，否则无法进行
        assert isinstance(hist_data, np.ndarray), \
            f'TypeError: expect np.ndarray as history segment, got {type(hist_data)} instead'
        # 将历史数据片段中的eps求均值，忽略Nan值,
        indices = hist_data.mean(axis=1).squeeze()
        print(f'in Selecting realize method got ranking vector like:\n {indices: .3f}')
        nan_count = np.isnan(indices).astype('int').sum()  # 清点数据，获取nan值的数量
        if largest_win:
            # 选择分数最高的部分个股，由于np排序时会把NaN值与最大值排到一起，因此需要去掉所有NaN值
            pos = max(share_count - pct - nan_count, 0)
        else:  # 选择分数最低的部分个股
            pos = pct
        # 对数据进行排序，并把排位靠前者的序号存储在arg_found中
        if distribution == 'even':
            # 仅当投资比例为均匀分配时，才可以使用速度更快的argpartition方法进行粗略排序
            arg_found = indices.argpartition(pos)[pos:]
        else:  # 如果采用其他投资比例分配方式时，必须使用较慢的全排序
            arg_found = indices.argsort()[pos:]
        # nan值数据的序号存储在arg_nan中
        arg_nan = np.where(np.isnan(indices))[0]
        # 使用集合操作从arg_found中剔除arg_nan，使用assume_unique参数可以提高效率
        args = np.setdiff1d(arg_found, arg_nan, assume_unique=True)
        # 构造输出向量，初始值为全0
        chosen = np.zeros_like(indices)
        # 根据投资组合比例分配方式，确定被选中产品的占比
        # Linear：根据分值排序线性分配，分值最高者占比约为分值最低者占比的三倍，其余居中者的比例按序呈等差数列
        if distribution == 'linear':
            dist = np.arange(1, 3, 2. / len(args))  # 生成一个线性序列，最大值为最小值的约三倍
            chosen[args] = dist / dist.sum()  # 将比率填入输出向量中
        # proportion：比例分配，占比与分值成正比，分值最低者获得一个基础比例，其余股票的比例与其分值成正比
        elif distribution == 'proportion':
            dist = indices[args]
            d = dist.max() - dist.min()
            if largest_win:
                dist = dist - dist.min() + d / 10.
            else:
                dist = dist.max() - dist + d / 10.
            chosen[args] = dist / dist.sum()
        # even：均匀分配，所有中选股票在组合中占比相同
        else:  # self.__distribution == 'even'
            chosen[args] = 1. / len(args)
        print(f'in Selecting realize method got share selecting vector like:\n {np.round(chosen,3)}')
        return chosen


BUILT_IN_STRATEGY_DICT = {'test':               TestTimingClass,
                          'crossline':          TimingCrossline,
                          'macd':               TimingMACD,
                          'dma':                TimingDMA,
                          'trix':               TimingTRIX,
                          'cdl':                TimingCDL,
                          'ricon_none':         RiconNone,
                          'urgent':             RiconUrgent,
                          'long':               TimingLong,
                          'short':              TimingShort,
                          'zero':               TimingZero,
                          's_dma':              SimpleDMA,
                          'all':                SelectingSimple,
                          'random':             SelectingRandom,
                          'finance':            SelectingFinance}

AVAILABLE_STRATEGIES = BUILT_IN_STRATEGY_DICT.keys()