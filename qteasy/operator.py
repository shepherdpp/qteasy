# coding=utf-8

import pandas as pd
import numpy as np
from qteasy.utilfuncs import sma, ema, trix, macd, cdldoji
from abc import abstractmethod, ABCMeta
from .history import HistoryPanel

class Strategy:
    """量化投资策略的抽象基类，所有策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的择时类调用"""
    __mataclass__ = ABCMeta
    # Strategy主类共有的属性
    _stg_type = 'strategy type'
    _stg_name = 'strategy name'
    _stg_text = 'intro text of strategy'
    _par_count = 0
    _par_types = []
    _par_bounds_or_enums = []

    @property
    def stg_type(self):
        return self._stg_type

    @property
    def stg_name(self):
        return self._stg_name

    @property
    def stg_text(self):
        return self._stg_text

    @property
    def par_count(self):
        return self._par_count

    @property
    def par_types(self):
        return self._par_types

    @property
    def par_boes(self):
        return self._par_bounds_or_enums

    @property
    def opt_tag(self):
        return self._opt_tag

    @property
    def pars(self):
        return self._pars

    # 以下是所有Strategy对象的共有方法
    def __init__(self, pars=None, opt_tag=0):
        # 对象属性：
        self._pars = pars
        self._opt_tag = opt_tag

    def info(self):
        # 打印所有相关信息和主要属性
        print('Type of Strategy:', self.stg_type)
        print('Information of the strategy:\n', self.stg_name, self.stg_text)
        print('Optimization Tag and opti ranges:', self.opt_tag, self.par_boes)
        if self._pars is not None:
            print('Parameter Loaded：', type(self._pars), self._pars)
        else:
            print('Parameter NOT loaded!')
        pass

    def set_pars(self, pars):
        self._pars = pars
        return pars

    def set_opt_tag(self, opt_tag):
        self._opt_tag = opt_tag
        return opt_tag

    def set_par_boes(self, par_boes):
        self._par_bounds_or_enums = par_boes
        return par_boes

    @abstractmethod
    def generate(self, hist_price):
        """策略类的基本抽象方法，接受输入参数并输出操作清单"""
        pass

# TODO: 以后可以考虑把Timing改为Alpha Model， Selecting改为Portfolio Manager， Ricon改为Risk Control
class Timing(Strategy):
    """择时策略的抽象基类，所有择时策略都继承自该抽象类，本类定义了generate抽象方法模版，供具体的择时类调用"""
    __mataclass__ = ABCMeta
    # Strategy主类共有的属性
    _stg_type = 'timing'
    data_freq = 'd'
    window_length = 270
    data_types = ['close']

    def __init__(self):
        super().__init__()

    ###################
    # 以下是本类型strategy对象的公共方法和抽象方法

    @abstractmethod
    def _generate_one(self, hist_pack, params):
        """抽象方法，在具体类中需要重写，是整个类的择时信号基本生成方法，针对单个个股的价格序列生成多空状态信号"""
        raise NotImplementedError

    def _generate_over(self, hist_slice:np.ndarray, pars:tuple):
        """ 中间构造函数，将历史数据模块传递过来的单只股票历史数据去除nan值，并进行滚动展开
            对于滚动展开后的矩阵，使用map函数循环调用generate_one函数生成整个历史区间的
            循环回测结果（结果为1维向量， 长度为hist_length - window_length + 1）

        input:
            :param hist_price:
        :return:
        """
        # 定位数据中的所有nan值，由于所有数据针对同一股票，因此nan值位置一致
        # 需要区别2D与1D数据，分别进行处理

        print(f'hist_slice got in Timing.generate_over() function is shaped {hist_slice.shape}')
        if len(hist_slice.shape) == 2:
            drop = ~np.isnan(hist_slice[:, 0])
        else:
            drop = ~np.isnan(hist_slice)
        # 生成输出值一维向量
        cat = np.zeros(hist_slice.shape[0])
        hist_nonan = hist_slice[drop]  # 仅针对非nan值计算，忽略股票停牌时期
        loop_count = len(hist_nonan) - self.window_length + 1
        if loop_count < 1:
            return cat

        # 开始进行历史数据的滚动真开
        hist_pack = np.zeros((loop_count, *hist_nonan[:self.window_length].shape))
        for i in range(loop_count):
            hist_pack[i] = hist_nonan[i:i + self.window_length]
        # 滚动展开完成，形成一个新的3D或2D矩阵
        # 开始将参数应用到策略实施函数generate中
        par_list = [pars] * loop_count
        res = np.array(list(map(self._generate_one,
                                hist_pack,
                                par_list)))

        capping = np.zeros(self.window_length - 1)
        print(f'in Timing.generate_over() function shapes of res and capping are {res.shape}, {capping.shape}')
        res = np.concatenate((capping, res), 0)
        cat[drop] = res
        return cat

    def generate(self, hist_data):
        """基于_generate_one方法生成整个股票价格序列集合的多空状态矩阵.

        本方法基于np的ndarray计算
        input：
            param: hist_extract：DataFrame，历史价格数据，需要被转化为ndarray
        return：=====
        """
        print(f'hist_data got in Timing.generate() function is shaped {hist_data.shape}')
        assert type(hist_data) is np.ndarray, f'Type Error: input should be ndarray, got {type(hist_data)}'
        assert hist_data.shape[1] >= self.window_length, \
            f'DataError: Not enough history data! expected hist data length {self.window_length},' \
            f' got {hist_data.shape[1]}'
        pars = self._pars
        if isinstance(pars, dict):
            par_list = pars.values()
        else:
            par_list = [pars] * hist_data.shape[0]  # 生成长度与shares数量相同的序列
        # 调用_generate_one方法计算单个个股的多空状态，并组合起来,3D与2D数据处理方式不同
        if len(hist_data.shape) == 3:
            # print(f'went through if fork hist_data - 3D')
            res = np.array(list(map(self._generate_over,
                                    hist_data,
                                    par_list))).T
        else:
            # print(f'went through if fork hist_data - 2D')
            res = np.array(list(map(self._generate_over,
                                    hist_data.T,
                                    par_list))).T
        print(f'generate result of np timing generate, result shaped {res.shape}')

        return res


class TimingSimple(Timing):
    """简单择时策略，返回整个历史周期上的恒定多头状态"""
    __stg_name = 'SIMPLE TIMING STRATEGY'
    __stg_text = 'Simple Timing strategy, return constant long position on the whole history'

    def _generate_one(self, hist_price, params):
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可

        return 1


class TimingCrossline(Timing):
    """crossline择时策略类，利用长短均线的交叉确定多空状态

        crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型

    """
    # 重写策略参数相关信息
    _par_count = 4
    _par_types = ['discr', 'discr', 'conti', 'enum']
    _par_bounds_or_enums = [(10, 250), (10, 250), (1, 100), ('buy', 'sell', 'none')]
    _stg_name = 'CROSSLINE STRATEGY'
    _stg_text = 'Moving average crossline strategy, determin long/short position according to the cross point of long and short term moving average prices'
    data_freq = 'd'
    window_length = 270
    data_types = ['close']

    def _generate_one(self, hist_price, params):
        """crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        s, l, m, hesitate = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T
        # 计算长短均线之间的距离
        diff = sma(h[0], l) - sma(h[0], s)
        # 根据观望模式在不同的点位产生Long/short标记
        if hesitate == 'buy':
            cat = np.where(diff < -m, 1, 0)
        elif hesitate == 'sell':
            cat = np.where(diff < m, 1, 0)
        else: # hesitate == 'none'
            cat = np.where(diff < 0, 1, 0)
        return cat[-1]


class TimingMACD(Timing):
    """MACD择时策略类，继承自Timing类，重写_generate方法'

    运用MACD均线策略，在hist_price Series对象上生成交易信号
    注意！！！
    由于MACD使用指数移动均线，由于此种均线的计算特性，在历史数据集的前max(sRange, lRange, mRange)
    个工作日上生成的数据不可用
    例如，max(sRange, lRange, mRange) = max(72,120,133) = 133个工作日内产生的买卖点不正确"""
    _par_count = 3
    _par_types = ['discr', 'discr', 'discr']
    _par_bounds_or_enums = [(10, 250), (10, 250), (10, 250)]
    _stg_name = 'MACD STRATEGY'
    _stg_text = 'MACD strategy, determin long/short position according to differences of exponential weighted moving average prices'
    data_freq = 'd'
    window_length = 270
    data_types = ['close']

    def _generate_one(self, hist_price, params):
        """生成单只个股的择时多空信号.

        输入:
            idx: 指定的参考指数历史数据
            sRange, 短均线参数，短均线的指数移动平均计算窗口宽度，单位为日
            lRange, 长均线参数，长均线的指数移动平均计算窗口宽度，单位为日
            dRange, DIFF的指数移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """

        s, l, m = params
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T

        # 计算指数的指数移动平均价格
        DIFF = ema(h[0], s) - ema(h[0], l)
        DEA = ema(DIFF, m)
        MACD = 2 * (DIFF - DEA)
        #DIFF, DEA, MACD = macd(hist_price, s, l, m)

        # 生成MACD多空判断：
        # 1， MACD柱状线为正，多头状态，为负空头状态：由于MACD = DIFF - DEA
        cat = np.where(MACD > 0, 1, 0)
        return cat[-1]


class TimingDMA(Timing):
    """DMA择时策略，继承自Timing类，重写_generate方法"""
    _par_count = 3
    _par_types = ['discr', 'discr', 'discr']
    _par_bounds_or_enums = [(10, 250), (10, 250), (10, 250)]
    _stg_name = 'quick-DMA STRATEGY'
    _stg_text = 'np based DMA strategy, determin long/short position according to differences of moving average prices'
    data_freq = 'd'
    window_length = 270
    data_types = ['close']

    def _generate_one(self, hist_price, params):
        # 使用基于np的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        # print 'Generating Quick DMA Long short Mask with parameters', params

        # 计算指数的移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T
        DMA = sma(h[0], s) - sma(h[0], l)
        AMA = DMA.copy()
        AMA[~np.isnan(DMA)] = sma(DMA[~np.isnan(DMA)], d)
        # print('qDMA generated DMA and AMA signal:', DMA.size, DMA, '\n', AMA.size, AMA)
        # 生成DMA多空判断：
        # 1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        # 2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        # 3， DMA与股价发生背离时的交叉信号，可信度较高
        cat = np.where(DMA > AMA, 1, 0)
        # print('qDMA generate category data with as type', cat.size, cat)
        return cat[-1]


class TimingTRIX(Timing):
    """TRIX择时策略，运用TRIX均线策略，利用历史序列上生成交易信号

    数据类型：close 收盘价，单数据输入
    数据分析频率：天
    数据窗口长度：270天
    参数数量：2个，参数类型：int整形，输入数据范围：[(10, 250), (10, 250)]
    """
    _par_count = 2
    _par_types = ['discr', 'discr']
    _par_bounds_or_enums = [(10, 250), (10, 250)]
    _stg_name = 'TRIX STRATEGY'
    _stg_text = 'TRIX strategy, determine long/short position according to triple exponential weighted moving average prices'
    data_freq = 'd'
    window_length = 270
    data_types = ['close']

    def _generate_one(self, hist_price, params):
        """参数:

        input:
        :param idx: 指定的参考指数历史数据
        :param sRange, 短均线参数，短均线的移动平均计算窗口宽度，单位为日
        :param mRange, DIFF的移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        """
        s, m = params
        # print 'Generating TRIX Long short Mask with parameters', params

        # 计算指数的指数移动平均价格
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = hist_price.T
        TRIX = trix(h[0], s)
        MATRIX = sma(TRIX, m)

        # 生成TRIX多空判断：
        # 1， TRIX位于MATRIX上方时，长期多头状态, signal = 1
        # 2， TRIX位于MATRIX下方时，长期空头状态, signal = 0
        cat = np.where(TRIX > MATRIX, 1, 0)
        return cat[-1]  # 返回时填充日期序列恢复nan值


class TimingCDL(Timing):
    """CDL择时策略，在K线图中找到符合要求的cdldoji模式

    数据类型：open, high, low, close 开盘，最高，最低，收盘价，多数据输入
    数据分析频率：天
    数据窗口长度：100天
    参数数量：0个，参数类型：N/A，输入数据范围：N/A
    """
    _par_count = 0
    _par_types = []
    _par_bounds_or_enums = []
    _stg_name = 'CDL INDICATOR STRATEGY'
    _stg_text = 'CDL Indicators, determine long/short position according to CDL Indicators'
    data_freq = 'd'
    window_length = 200
    data_types = ['open', 'high', 'low', 'close']

    def _generate_one(self, hist_price, params=None):
        """参数:

        input:
            None
        """
        # 计算历史数据上的CDL指标
        h = hist_price.T
        cat = (cdldoji(h[0], h[1], h[2], h[3]).cumsum() // 100)

        return float(cat[-1])


class Selecting(Strategy):
    """选股策略类的抽象基类，所有选股策略类都继承该类"""
    __metaclass__ = ABCMeta
    # Strategy主类共有的属性
    _stg_type = 'selecting'

    #######################
    # Selecting 类的自有方法和抽象方法

    @abstractmethod
    def _select(self, shares, date, pct):
        # Selecting 类的选股抽象方法，在不同的具体选股类中应用不同的选股方法，实现不同的选股策略
        # 返回值：代表一个周期内股票选择权重的ndarray，1Darray
        pass

    def __to_trade_day(self, date):
        # 如果给定日期是交易日，则返回该日期，否则返回该日期的后一个交易日
        # 有可能传入的date参数带有时间部分，无法与交易日清单中的纯日期比较，因此需要转化为纯日期
        # 使用astype将带有时间的datetime64格式转化为纯日期的datetime64
        if self.__trade_cal.loc[date.astype('<M8[D]')] == 1:
            return date
        else:
            while self.__trade_cal.loc[date.astype('<M8[D]')] != 1:
                date = date + np.timedelta64(1, 'D')
            return date

    def __to_prev_trade_day(self, date):
        # 韩惠给定日期的前一个交易日
        # 使用astype将带有时间的datetime64格式转化为纯日期的datetime64
        date = date - np.timedelta64(1, 'D')
        while self.__trade_cal.loc[date.astype('<M8[D]')] != 1:
            date = date - np.timedelta64(1, 'D')
        return date

    def _seg_periods(self, dates, freq):
        # 对输入的价格序列数据进行分段，Selection类会对每个分段应用不同的股票组合
        # 对输入的价格序列日期进行分析，生成每个历史分段的起止日期所在行号，并返回行号和分段长度（数据行数）
        # 输入：
        # dates ndarray，日期序列，
        # freq：str 分段频率，取值为‘Q'：季度， ’Y'，年度； ‘M'，月度
        # 输出：=====
        # seg_pos: 每一个历史分段的开始日期;
        # seg_lens：每一个历史分段中含有的历史数据数量，
        # en(seg_lens): 分段的数量
        # 生成历史区间内的时间序列，序列间隔为选股间隔，每个时间点代表一个选股区间的开始时间
        bnds = pd.date_range(start=dates[0], end=dates[-1], freq=freq).values
        # 写入第一个选股区间分隔位——0
        seg_pos = np.zeros(shape=(len(bnds) + 2), dtype='int')
        print(f'in module selecting: function set_perids: comparing {dates[0]} and {bnds[0]}')
        seg_pos[1:-1] = np.searchsorted(dates, bnds)
        # 最后一个分隔位等于历史区间的总长度
        seg_pos[-1] = len(dates) - 1
        # print('Results check, selecting - segment creation, segments:', seg_pos)
        # 计算每个分段的长度
        seg_lens = (seg_pos - np.roll(seg_pos, 1))[1:]
        return seg_pos, seg_lens, len(seg_pos) - 1

    def generate(self, hist_price, dates, shares):
        """
        生成历史价格序列的选股组合信号：将历史数据分成若干连续片段，在每一个片段中应用某种规则建立投资组合
        建立的投资组合形成选股组合蒙版，每行向量对应所有股票在当前时间点在整个投资组合中所占的比例
        输入：
        hist_price：历史数据, DataFrame
        输出：=====sel_mask：选股蒙版，是一个与输入历史数据尺寸相同的ndarray，dtype为浮点数，取值范围在0～1之间
         矩阵中的取值代表股票在投资组合中所占的比例，0表示投资组合中没有该股票，1表示该股票占比100%
        获取参数

        :param hist_price: type: np.ndarray, 历史数据
        :param dates:
        :param shares:
        :return:
        """

        freq = self._pars[0]
        poq = self._pars[1]
        # 获取完整的历史日期序列，并按照选股频率生成分段标记位，完整历史日期序列从参数获得，股票列表也从参数获得
        # dates = hist_price.index.values
        # print('SPEED TEST Selection module, Time of segmenting history')
        # %time self._seg_periods(dates, freq)
        assert isinstance(hist_price, np.ndarray), 'Type Error: input historical data should be ndarray'
        seg_pos, seg_lens, seg_count = self._seg_periods(dates, freq)
        # shares = hist_price.columns
        # 一个空的list对象用于存储生成的选股蒙版
        sel_mask = np.zeros(shape=(len(dates), len(shares)), order='C')
        seg_start = 0

        for sp, sl in zip(seg_pos, seg_lens):  # 针对每一个选股分段区间内生成股票在投资组合中所占的比例
            # share_sel向量代表当前区间内的投资组合比例
            share_sel = self._select(shares, dates[sp], poq)
            seg_end = seg_start + sl
            # 填充相同的投资组合到当前区间内的所有交易时间点
            sel_mask[seg_start:seg_end + 1, :] = share_sel
            seg_start = seg_end
        # 将所有分段组合成完整的ndarray
        # print('SPEED TEST selection module, time of concatenating segments')
        return sel_mask


class SelectingTrend(Selecting):
    """趋势选股策略，继承自选股策略类"""
    _stg_name = 'TREND SELECTING'
    _stg_text = 'Selecting share according to detected trends'

    def _select(self, shares, date, pct):
        # 所有股票全部被选中，权值（投资比例）平均分配
        return [1. / len(shares)] * len(shares)

    pass


class SelectingSimple(Selecting):
    """基础选股策略：保持历史股票池中的所有股票都被选中，投资比例平均分配"""
    _stg_name = 'SIMPLE SELECTING'
    _stg_text = 'Selecting all share and distribute weights evenly'

    def _select(self, shares, date, pct):
        # 所有股票全部被选中，投资比例平均分配
        return [1. / len(shares)] * len(shares)


class SelectingRandom(Selecting):
    """基础选股策略：在每个历史分段中，按照指定的概率（p<1时）随机抽取若干股票，或随机抽取指定数量（p>1）的股票进入投资组合，投资比例平均分配"""
    _stg_name = 'RANDOM SELECTING'
    _stg_text = 'Selecting share Randomly and distribute weights evenly'

    def _select(self, shares, date, par):
        if par < 1:
            # 给定参数小于1，按照概率随机抽取若干股票
            chosen = np.random.choice([1, 0], size=len(shares), p=[par, 1 - par])
        else:  # par >= 1 给定参数大于1，抽取给定数量的股票
            choose_at = np.random.choice(len(shares), size=(int(par)), replace=False)
            chosen = np.zeros(len(shares))
            chosen[choose_at] = 1
        return chosen.astype('float') / chosen.sum()  # 投资比例平均分配


class SelectingRanking(Selecting):
    """
    普遍适用的选股策略：根据事先定义的排序表（Ranking table）来选择股票，根据不同的参数可以自定义多种不同的选股方式
    相关选股参数保存为对象属性，在Further_initialization过程中初始化, 包括：
        self.__ranking_table: 排序表，策略核心。在一张表中列出所有股票在不同历史时期的评分值，根据评分值的排序确定投资组合中的股票
        self.__largest_win: 布尔变量，为True时优先选择分值最高的股票，否则优先选择分值最低的股票
        self.__distribution: str变量，指定如何确定中选股票在投资组合中的比例：
            'even': 均匀分配，所有中选股票比例相同
            'linear': 线性分配，中选股票在组合中的占比呈等差数列，排名最高者比最低者比例高约200%
            'proportion': 比例分配，中选股票在组合中的占比与其分值成正比
        self.__drop_threshold: 弃置阈值，当分值低于（或高于）该阈值时将股票从组合中剔除'''
    """
    _stg_name = 'RANKING SELECTING'
    _stg_text = 'Selecting shares according to the so called ranking table, distribute weights in multiple ways'
    _par_count = 3  # 比普通selecting多一个ranking_table参数，opt类型为enum（自然）
    _par_types = ['enum', 'conti', 'enum']
    _par_bounds_or_enums = [('M', 'Q', 'S', 'Y'), (0, 1), ()]  # 四种分组单元分别为 'month', 'quarter', 'semi', 'year'

    # TODO: 因为Strategy主类代码重构，ranking table的代码结构也应该相应修改，待修改
    # 重写参数设置方法，把增加的策略参数包含在内
    def set_param(self, freq=None, pct_or_qty=None, ranking_table=None, largest_win=True, distribution='even',
                  drop_threshold=None):
        if freq is None:
            self.__freq = 'Q'
        else:
            self.__freq = freq
        if pct_or_qty is None:
            self.__pct_or_qty = 0.5
        else:
            self.__pct_or_qty = pct_or_qty
        self.__ranking_table = ranking_table
        self.__largest_win = largest_win
        self.__distribution = distribution
        self.__drop_threshold = drop_threshold
        pass

    # 重写信息打印方法，增加新增的策略参数
    def info(self):
        # 打印所有相关信息和主要属性
        print('Here\'s information of the Selecting strategy:', self.StgName, self.StgText, sep='\n')
        print('key parameters: frequency and selection percent or quantity', self.__freq,
              self.__pct_or_qty,
              sep='\n')
        if not self.__ranking_table is None:
            print('Other key parameters: \n', 'ranking table, largest win, distribution, drop threshold \n',
                  type(self.__ranking_table), self.__largest_win, self.__distribution, self.__drop_threshold,
                  sep=',')
        else:
            print('Other key parameters: \n', 'ranking table, largest win, distribution, drop threshold \n',
                  'Ranking Table None', self.__largest_win, self.__distribution, self.__drop_threshold,
                  sep=',')

    def _select(self, shares, date, par):
        """# 根据事先定义的排序表根据不同的方法选择一定数量的股票
    # 输入：
        # shares：列表，包含了所有备选投资产品的代码
        # date：选股日期，选股操作发生的日期
        # par：选股参数，选股百分比或选股数量
    # 输出：=====
        # chosen：浮点型向量，元素数量与shares中的相同，每个元素代表对应的投资产品在投资组合中占的比例"""
        share_count = len(shares)
        if par < 1:
            # par 参数小于1时，代表目标投资组合在所有投资产品中所占的比例，如0.5代表需要选中50%的投资产品
            par = int(len(shares) * par)
        else:  # par 参数大于1时，取整后代表目标投资组合中投资产品的数量，如5代表需要选中5只投资产品
            par = int(par)
        if not self.__ranking_table is None:  # 排序表不能为空，否则无法进行
            # 排序表的列名为每一列数据的可用日期，也就是说该列数据只在该日期以后可用，获取可用日期
            r_table_dates = self.__ranking_table.columns
            # 根据选股日期选择最为接近的数据可用日期，用于确定使用哪一列数据执行选股操作
            i = r_table_dates.searchsorted(date)
            indices = self.__ranking_table[r_table_dates[i]]  # 定位到i列数据
            # 排序表的行索引为所有投资产品的代码，提取出shares列表中股票的分值，并压缩维度到1维
            indices = indices.loc[shares].values.squeeze()
            nan_count = np.isnan(indices).astype('int').sum()  # 清点数据，获取nan值的数量
            if self.__largest_win:
                # 选择分数最高的部分个股，由于np排序时会把NaN值与最大值排到一起，因此需要去掉所有NaN值
                pos = max(share_count - par - nan_count, 0)
            else:  # 选择分数最低的部分个股
                pos = par
            # 对数据进行排序，并把排位靠前者的序号存储在arg_found中
            if self.__distribution == 'even':
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
            if self.__distribution == 'linear':
                dist = np.arange(1, 3, 2. / len(args))  # 生成一个线性序列，最大值为最小值的约三倍
                chosen[args] = dist / dist.sum()  # 将比率填入输出向量中
            # proportion：比例分配，占比与分值成正比，分值最低者获得一个基础比例，其余股票的比例与其分值成正比
            elif self.__distribution == 'proportion':
                dist = indices[args]
                d = dist.max() - dist.min()
                if self.__largest_win:
                    dist = dist - dist.min() + d / 10.
                else:
                    dist = dist.max() - dist + d / 10.
                chosen[args] = dist / dist.sum()
            # even：均匀分配，所有中选股票在组合中占比相同
            else:  # self.__distribution == 'even'
                chosen[args] = 1. / len(args)
            return chosen
        else:
            # 排序表不存在，返回包含所有股票平均分配比例的投资组合
            return [1. / len(shares)] * len(shares)
        pass

    def ranking_table(self, r_table=None):
        # 给ranking_table属性赋值，或者打印当前ranking_table的信息
        if r_table is None:  # 打印当前ranking_table的信息
            if self.__ranking_table is None:
                print('ranking table does not exist!')
                print('ranking table must be created before ranking based selection')
            else:
                print('ranking table information', self.__ranking_table.info())
        else:  # 将传入的数据赋值给对象的ranking_table属性
            self.__ranking_table = r_table


class Ricon(Strategy):
    """风险控制抽象类，所有风险控制策略均继承该类"""
    '''该策略仅仅生成卖出信号，无买入信号，因此作为止损点控制策略，仅与其他策略配合使用'''
    __metaclass__ = ABCMeta
    _stg_type = 'RiCon'

    @abstractmethod
    def generate(self, hist_price):
        pass


class RiconNone(Ricon):
    """无风险控制策略，不对任何风险进行控制"""
    _stg_name = 'NONE'
    _stg_text = 'Do not take any risk control activity'

    def generate(self, hist_price):
        return np.zeros_like(hist_price)


class RiconUrgent(Ricon):
    """urgent风控类，继承自Ricon类，重写_generate_ricon方法"""
    # 跌幅控制策略，当N日跌幅超过p%的时候，强制生成卖出信号
    _par_count = 2
    _par_types = ['discr', 'conti']
    _par_bounds_or_enums = [(1, 40), (-0.5, 0.5)]
    _stg_name = 'URGENT'
    _stg_text = 'Generate selling signal when N-day drop rate reaches target'

    def generate(self, hist_price):
        """
        # 根据N日内下跌百分比确定的卖出信号，让N日内下跌百分比达到pct时产生卖出信号

        input =====
            :type hist_price: tuple like (N, pct): type N: int, Type pct: float
                输入参数对，当股价在N天内下跌百分比达到pct时，产生卖出信号
        return ====
            :rtype: object np.ndarray: 包含紧急卖出信号的ndarray
        """
        assert self._pars is not None, 'Parameter of Risk Control-Urgent should be a pair of numbers like (N, ' \
                                       'pct)\nN as days, pct as percent drop '
        assert isinstance(hist_price, np.ndarray), 'Type Error: input historical data should be ndarray'
        day, drop = self._pars
        h = hist_price[:,:,0].T
        print(f'input array got in Ricon.generate() is shaped {hist_price.shape}')
        print(f'and the hist_data is converted to shape {h.shape}')
        diff = (h - np.roll(h, day)) / h
        print(f'created array in ricon generate() is shaped {diff.shape}')
        return np.where(diff < drop, -1, 0)


def _mask_to_signal(lst):
    """将持仓蒙板转化为交易信号.

    转换的规则为比较前后两个交易时间点的持仓比率，如果持仓比率提高，
    则产生相应的补仓买入信号；如果持仓比率降低，则产生相应的卖出信号将仓位降低到目标水平。
    生成的信号范围在(-1, 1)之间，负数代表卖出，正数代表买入，且具体的买卖信号signal意义如下：
        signal > 0时，表示用总资产的 signal * 100% 买入该资产， 如0.35表示用当期总资产的35%买入该投资产品，如果
            现金总额不足，则按比例调降买入比率，直到用尽现金。
        signal < 0时，表示卖出本期持有的该资产的 signal * 100% 份额，如-0.75表示当期应卖出持有该资产的75%份额。
        signal = 0时，表示不进行任何操作

    输入：
        参数 lst，ndarray，持仓蒙板
    输出：=====
        op，ndarray，交易信号矩阵
    """

    # 比较本期交易时间点和上期之间的持仓比率差额，差额大于0者可以直接作为补仓买入信号，如上期为0.35，
    # 本期0.7，买入信号为0.35，即使用总资金的35%买入该股，加仓到70%
    op = (lst - np.roll(lst, 1))
    # 差额小于0者需要计算差额与上期持仓数之比，作为卖出信号的强度，如上期为0.7，本期为0.35，差额为-0.35，则卖出信号强度
    # 为 (0.7 - 0.35) / 0.35 = 0.5即卖出50%的持仓数额，从70%仓位减仓到35%
    op = np.where(op < 0, (op / np.roll(lst, 1)), op)
    # 补齐因为计算差额导致的第一行数据为NaN值的问题
    op[0] = lst[0]
    return op


def _legalize(lst):
    """交易信号合法化，整理生成的交易信号，使交易信号符合规则.

    根据历史数据产生的交易信号不一定完全符合实际的交易规则，在必要时需要对交易信号进行
    修改，以确保最终的交易信号符合交易规则，这里的交易规则仅包含与交易时间相关的规则如T+1规则等，与交易
    成本或交易量相关的规则如费率、MOQ等都在回测模块中考虑"""

    # 最基本的操作规则是不允许出现大于1或者小于-1的交易信号
    return lst.clip(-1, 1)


def _timing_blend_change(ser: np.ndarray):
    """
    this method is based on np thus is faster than the other two

    :type ser: object np.ndarray
    """
    if ser[0] > 0:
        state = 1
    else:
        state = 0
    res = np.zeros_like(ser)
    prev = ser[0]
    for u, v in np.nditer([res, ser], op_flags=['readwrite']):
        if v < prev:
            state = 0
        elif v > prev:
            state = 1
        u[...] = state
        prev = v
    return res


def _blend(n1, n2, op):
    """混合操作符函数，使用加法和乘法处理与和或的问题,可以研究逻辑运算和加法运算哪一个更快，使用更快的一个

    input:
        :param n1: np.ndarray: 第一个输入矩阵
        :param n2: np.ndarray: 第二个输入矩阵
        :param op: np.ndarray: 运算符
    return:
        :return: np.ndarray

    """
    if op == 'or':
        return n1 + n2
    elif op == 'and':
        return n1 * n2


def unify(arr):
    """
    unify each row of input array so that the sum of all elements in one row is 1, and each element remains
    its original ratio to the sum
    调整输入矩阵每一行的元素，使得所有元素等比例缩小（或放大）后的和为1

    example:
    unify([[3.0, 2.0, 5.0], [2.0, 3.0, 5.0]])
    =
    [[0.3, 0.2, 0.5], [0.2, 0.3, 0.5]]

    :param arr: type: np.ndarray
    :return: ndarray
    """
    assert isinstance(arr, np.ndarray), 'Input should be ndarray!'
    s = arr.sum(1)
    shape = (s.shape[0], 1)
    return arr / s.reshape(shape)


class Operator:
    """交易操作生成类，通过简单工厂模式创建择时属性类和选股属性类，并根据这两个属性类的结果生成交易清单

    交易操作生成类包含若干个选股对象组件，若干个择时对象组件，以及若干个风险控制组件，所有这些组件对象都能
    在同一组历史数据对象上进行相应的选股操作、择时操作并进行风控分析。不同的选股或择时对象工具独立地在历史数据
    对象上生成选股蒙版或多空蒙版，这些独立的选股蒙版及多空蒙版又由不同的方式混合起来（通过交易操作对象的蒙版
    混合属性确定，其中选股蒙版混合属性是一个逻辑表达式，根据这个逻辑表达式用户可以确定所有的蒙版的混合方式，
    例如“0 or （ 1 and （ 2 and 3 ） or 4 ）”；多空信号的生成方式是三个生成选项之一）。生成一个
    综合应用所有择时选股风控策略在目标历史数据上后生成的一个交易信号记录，交易信号经过合法性修改后成为
    一个最终输出的合法交易记录（信号）

    """

    # 对象初始化时需要给定对象中包含的选股、择时、风控组件的类型列表
    def __init__(self, selecting_types=None,
                 timing_types=None,
                 ricon_types=None):
        # 根据输入的参数生成择时具体类:
        # 择时类的混合方式有：
        # pos-N：只有当大于等于N个策略看多时，输出为看多，否则为看空
        # chg-N：在某一个多空状态下，当第N个反转信号出现时，反转状态
        # cumulate：没有绝对的多空状态，给每个策略分配同样的权重，当所有策略看多时输出100%看多，否则
        # 输出的看多比例与看多的策略的权重之和相同，当多空状态发生变化时会生成相应仓位的交易信号
        # 对象属性：
        # 交易信号通用属性：
        self.__Tp0 = False  # 是否允许T+0交易，True时允许T+0交易，否则不允许
        # 交易策略属性：
        # 对象的timings属性和timing_types属性都是列表，包含若干策略而不是一个策略
        if selecting_types is None:
            selecting_types = ['simple']
        if timing_types is None:
            timing_types = ['simple']
        if ricon_types is None:
            ricon_types = ['none']
        self.__timing_types = []
        self.__timing = []
        self.__timing_blender = 'pos-1'  # 默认的择时策略混合方式
        # print timing_types
        for timing_type in timing_types:
            # print timing_type.lower()
            # 通过字符串比较确认timing_type的输入参数来生成不同的具体择时策略对象，使用.lower()转化为全小写字母
            self.__timing_types.append(timing_type)
            if timing_type.lower() == 'cross_line':
                self.__timing.append(TimingCrossline())
            elif timing_type.lower() == 'macd':
                self.__timing.append(TimingMACD())
            elif timing_type.lower() == 'dma':
                self.__timing.append(TimingDMA())
            elif timing_type.lower() == 'trix':
                self.__timing.append(TimingTRIX())
            elif timing_type.lower() == 'cdl':
                self.__timing.append(TimingCDL())
            else:  # 默认情况下使用simple策略
                self.__timing.append(TimingSimple())
                self.__timing_types.pop()
                self.__timing_types.append('simple')
                # print timing_type
        # 根据输入参数创建不同的具体选股策略对象。selecting_types及selectings属性与择时策略对象属性相似
        # 都是列表，包含若干相互独立的选股策略（至少一个）
        self.__selecting_type = []
        self.__selecting = []
        # 选股策略的混合方式使用以下字符串描述。简单来说，每个选股策略都独立地生成一个选股蒙版，每个蒙版与其他的
        # 蒙版的混合方式要么是OR（+）要么是AND（*），最终混合的结果取决于这些蒙版的混合方法和混合顺序而多个蒙版
        # 的混合方式就可以用一个类似于四则运算表达式的方式来描述，例如“（ 0 + 1 ） * （ 2 + 3 * 4 ）”
        # 在操作生成模块中，有一个表达式解析器，通过解析四则运算表达式来解算selecting_blender_string，并将混
        # 合的步骤以前缀表达式的方式存储在selecting_blender中，在混合时按照前缀表达式的描述混合所有蒙版。注意
        # 表达式中的数字代表selectings列表中各个策略的索引值
        cur_type = 0
        self.__selecting_blender_string = ''
        for selecting_type in selecting_types:
            self.__selecting_type.append(selecting_type)
            if cur_type == 0:
                self.__selecting_blender_string += str(cur_type)
            else:
                self.__selecting_blender_string += ' or ' + str(cur_type)
            cur_type += 1
            if selecting_type.lower() == 'trend':
                self.__selecting.append(SelectingTrend())
            elif selecting_type.lower() == 'random':
                self.__selecting.append(SelectingRandom())
            elif selecting_type.lower() == 'ranking':
                self.__selecting.append(SelectingRanking())
            else:
                self.__selecting.append(SelectingSimple())
                self.__selecting_type.pop()
                self.__selecting_type.append('simple')
            # create selecting blender by selecting blender string
            self.__selecting_blender = self._exp_to_blender

        # 根据输入参数生成不同的风险控制策略对象
        self.__ricon_type = []
        self.__ricon = []
        self.__ricon_blender = 'add'
        for ricon_type in ricon_types:
            self.__ricon_type.append(ricon_type)
            if ricon_type.lower() == 'none':
                self.__ricon.append(RiconNone())
            elif ricon_type.lower() == 'urgent':
                self.__ricon.append(RiconUrgent())
            else:
                self.__ricon.append(RiconNone())
                self.__ricon_type.append('none')

    @property
    def timing(self):
        return self.__timing

    @property
    def selecting(self):
        return self.__selecting

    @property
    def ricon(self):
        return self.__ricon

    @property
    def strategies(self):
        stg = []
        stg.extend(self.timing)
        stg.extend(self.selecting)
        stg.extend(self.ricon)
        return stg

    # Operation对象有两类属性需要设置：blender混合器属性、Parameters策略参数或属性
    # 这些属性参数的设置需要在OP模块设置一个统一的设置入口，同时，为了实现与Optimizer模块之间的接口
    # 还需要创建两个Opti接口函数，一个用来根据的值创建合适的Space初始化参数，另一个用于接受opt
    # 模块传递过来的参数，分配到合适的策略中去
    #TODO: convert all parameter setting functions to private except one single entry-function set_parameter()
    def set_blender(self, blender_type, *args, **kwargs):
        # 统一的blender混合器属性设置入口
        if type(blender_type) == str:
            if blender_type.lower() == 'selecting':
                self.__set_selecting_blender(*args, **kwargs)
            elif blender_type.lower() == 'timing':
                self.__set_timing_blender(*args, **kwargs)
            elif blender_type.lower() == 'ricon':
                self.__set_ricon_blender(*args, **kwargs)
            else:
                print('wrong input!')
                pass
        else:
            print('blender_type should be a string')
        pass

    def set_parameter(self, stg_id, pars=None, opt_tag=None, par_boes=None):
        """统一的策略参数设置入口，stg_id标识接受参数的具体成员策略
           stg_id的格式为'x-n'，其中x为's/t/r'中的一个字母，n为一个整数

           :param stg_id:
           :param pars:
           :param opt_tag:
           :param par_boes:
           :return:

        """
        if type(stg_id) == str:
            l = stg_id.split('-')
            stg = l[0]
            num = int(l[1])
            if stg.lower() == 's':
                strategy = self.selecting[num]
            elif stg.lower() == 't':
                strategy = self.timing[num]
            elif stg.lower() == 'r':
                strategy = self.ricon[num]
            else:
                print('wrong input!')
                return None
            if pars is not None:
                strategy.set_pars(pars)
            if opt_tag is not None:
                strategy.set_opt_tag(opt_tag)
            if par_boes is not None:
                strategy.set_par_boes(par_boes)
        else:
            print('blender_type should be a string')
        pass

    def _set_opt_par(self, opt_par):
        # 将输入的opt参数切片后传入stg的参数中
        s = 0
        k = 0
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass
            elif stg.opt_tag == 1:
                k += stg.par_count
                stg.set_pars(opt_par[s:k])
                s = k
            elif stg.opt_tag == 2:
                k += 1
                stg.set_pars(opt_par[s:k])
                s = k

    def get_opt_space_par(self):
        ranges = []
        types = []
        for stg in self.strategies:
            if stg.opt_tag == 0:
                pass  # 策略优化方案关闭
            elif stg.opt_tag == 1:
                ranges.extend(stg.par_boes)
                types.extend(stg.par_types)
            elif stg.opt_tag == 2:
                ranges.append(stg.par_boes)
                types.extend(['enum'])
        return ranges, types
        pass

    # =================================================
    # 下面是Operation模块的公有方法：
    def info(self):
        """# 打印出当前交易操作对象的信息，包括选股、择时策略的类型，策略混合方法、风险控制策略类型等等信息
        # 如果策略包含更多的信息，还会打印出策略的一些具体信息，如选股策略的信息等
        # 在这里调用了私有属性对象的私有属性，不应该直接调用，应该通过私有属性的公有方法打印相关信息
        # 首先打印Operation木块本身的信息"""
        print('OPERATION MODULE INFO:')
        print('=' * 25)
        print('Information of the Module')
        print('=' * 25)
        # 打印各个子模块的信息：
        # 首先打印Selecting模块的信息
        print('Total count of Selecting strategies:', len(self.__selecting))
        print('the blend type of selecting strategies is', self.__selecting_blender_string)
        print('Parameters of Selecting Strategies:')
        for sel in self.selecting:
            sel.info()
        print('#' * 25)

        # 接着打印 timing模块的信息
        print('Total count of timing strategies:', len(self.__timing))
        print('The blend type of timing strategies is', self.__timing_blender)
        print('Parameters of timing Strategies:')
        for tmg in self.timing:
            tmg.info()
        print('#' * 25)

        # 最后打印Ricon模块的信息
        print('Total count of Risk Control strategies:', len(self.__ricon))
        print('The blend type of Risk Control strategies is', self.__ricon_blender)
        for ric in self.ricon:
            ric.info()
        print('#' * 25)

    # TODO： 目前的三维数据处理方式是：将整个3D historyPanel传入策略，在策略的generate方法所调用的最底层（Timing的generate_one, \
    # TODO：Selecting的select方法等）对历史数据框架进行切片操作，提取出正确的数据。这种方法只是临时应用，最终的应用方式应该是在最外层 \
    # TODO：就将数据切片后传入，这样在策略最内层的自定义方法中不用关心数据的格式和切片问题，只需要定义好数据类型htypes参数就可以了
    def create(self, hist_data:HistoryPanel):
        """# 操作信号生成方法，在输入的历史数据上分别应用选股策略、择时策略和风险控制策略，生成初步交易信号后，
        # 对信号进行合法性处理，最终生成合法交易信号
        # 输入：
            # hist_data：从数据仓库中导出的历史数据，包含多只股票在一定时期内特定频率的一组或多组数据
        # 输出：=====
            # lst：使用对象的策略在历史数据期间的一个子集上产生的所有合法交易信号，该信号可以输出到回测
            # 模块进行回测和评价分析，也可以输出到实盘操作模块触发交易操作
        #print( 'Time measurement: selection_mask creation')
        # 第一步，在历史数据上分别使用选股策略独立产生若干选股蒙板（sel_mask）
        # 选股策略的所有参数都通过对象属性设置，因此在这里不需要传递任何参数"""
        sel_masks = []
        assert isinstance(hist_data, HistoryPanel), \
            f'Type Error: historical data should be HistoryPanel, got {type(hist_data)}'
        shares = hist_data.levels
        data_types = hist_data.htypes
        date_list = list(hist_data.index.keys())
        # print(f'date_list is {date_list}')
        h_v = hist_data.values
        print(f'shape of h_v in operator.create() function: {h_v.shape}')
        for sel in self.__selecting:  # 依次使用选股策略队列中的所有策略逐个生成选股蒙板
            # print('SPEED test OP create, Time of sel_mask creation')
            sel_masks.append(sel.generate(h_v, date_list, shares))  # 生成的选股蒙板添加到选股蒙板队列中
        # print('SPEED test OP create, Time of sel_mask blending')
        # %time (self.__selecting_blend(sel_masks))
        sel_mask = self.__selecting_blend(sel_masks)  # 根据蒙板混合前缀表达式混合所有蒙板
        print(f'Sel_mask has been created! shape is {sel_mask.shape}')
        # sel_mask.any(0) 生成一个行向量，每个元素对应sel_mask中的一列，如果某列全部为零，该元素为0，
        # 乘以hist_extract后，会把它对应列清零，因此不参与后续计算，降低了择时和风控计算的开销
        selected_shares = sel_mask.any(0)
        # TODO: 这里本意是筛选掉未中选的股票，降低择时计算的开销，使用新的数据结构后不再适用，需改进以使其适用
        # hist_selected = hist_data * selected_shares
        # print ('Time measurement: ls_mask creation')
        # 第二步，使用择时策略在历史数据上独立产生若干多空蒙板(ls_mask)
        ls_masks = []
        for tmg in self.__timing:  # 依次使用择时策略队列中的所有策略逐个生成多空蒙板
            # 生成多空蒙板时忽略在整个历史考察期内从未被选中过的股票：
            # print('SPEED test OP create, Time of ls_mask creation')
            ls_masks.append(tmg.generate(h_v))
            # print(tmg.generate(h_v))
            # print('ls mask created: ', tmg.generate(hist_selected).iloc[980:1000])
        # print('SPEED test OP create, Time of ls_mask blending')
        # %time self.__timing_blend(ls_masks)
        ls_mask = self.__timing_blend(ls_masks)  # 混合所有多空蒙板生成最终的多空蒙板
        print(f'Long/short_mask has been created! shape is {ls_mask.shape}')
        # print( '\n long/short mask: \n', ls_mask)
        # print 'Time measurement: risk-control_mask creation'
        # 第三步，风险控制交易信号矩阵生成（简称风控矩阵）
        ricon_mats = []
        for ricon in self.__ricon:  # 依次使用风控策略队列中的所有策略生成风险控制矩阵
            # print('SPEED test OP create, Time of ricon_mask creation')
            ricon_mats.append(ricon.generate(h_v))  # 所有风控矩阵添加到风控矩阵队列
        # print('SPEED test OP create, Time of ricon_mask blending')
        # %time self.__ricon_blend(ricon_mats)
        ricon_mat = self.__ricon_blend(ricon_mats)  # 混合所有风控矩阵后得到最终的风控策略
        print(f'risk control_mask has been created! shape is {ricon_mat.shape}')
        # print ('risk control matrix \n', ricon_mat[980:1000])
        # print (ricon_mat)
        # print ('sel_mask * ls_mask: ', (ls_mask * sel_mask))
        # 使用mask_to_signal方法将多空蒙板及选股蒙板的乘积（持仓蒙板）转化为交易信号，再加上风控交易信号矩阵，并对交易信号进行合法化
        # print('SPEED test OP create, Time of operation mask creation')
        # %time self._legalize(self._mask_to_signal(ls_mask * sel_mask) + (ricon_mat))
        op_mat = _legalize(_mask_to_signal(ls_mask * sel_mask) + ricon_mat)
        print(f'Finally op mask has been created, shaped {op_mat.shape}')
        # pd.DataFrame(op_mat, index = date_list, columns = shares)
        lst = pd.DataFrame(op_mat, index=date_list, columns=shares)
        # print ('operation matrix: ', '\n', lst.loc[lst.any(axis = 1)]['2007-01-15': '2007-03-01'])
        # return lst[lst.any(1)]
        # 消除完全相同的行和数字全为0的行
        lst_out = lst[lst.any(1)]
        keep = (lst_out - lst_out.shift(1)).any(1)
        return lst_out[keep]

        ################################################################

    # ================================
    # 下面是Operation模块的私有方法

    def __set_timing_blender(self, timing_blender):
        """设置择时策略混合方式，混合方式包括pos-N,chg-N，以及cumulate三种

        输入：
            参数 timing_blender，str，合法的输入包括：
                'chg-N': N为正整数，取值区间为1到len(timing)的值，表示多空状态在第N次信号反转时反转
                'pos-N': N为正整数，取值区间为1到len(timing)的值，表示在N个策略为多时状态为多，否则为空
                'cumulate': 在每个策略发生反转时都会产生交易信号，但是信号强度为1/len(timing)
        输出：=====
            无
        """
        self.__timing_blender = timing_blender

    def __set_selecting_blender(self, selecting_blender_expression):
        # 设置选股策略的混合方式，混合方式通过选股策略混合表达式来表示
        # 给选股策略混合表达式赋值后，直接解析表达式，将选股策略混合表达式的前缀表达式存入选股策略混合器
        if not type(selecting_blender_expression) is str:  # 如果输入不是str类型
            self.__selecting_blender = self._exp_to_blender
            self.__selecting_blender_string = '0'
        else:
            self.__selecting_blender = self._exp_to_blender
            self.__selecting_blender_string = selecting_blender_expression

    def __set_ricon_blender(self, ricon_blender):
        self.__ricon_blender = ricon_blender

    def __timing_blend(self, ls_masks):
        """# 择时策略混合器，将各个择时策略生成的多空蒙板按规则混合成一个蒙板
        # input：=====
            :type: ls_masks：object ndarray, 多空蒙板列表，包含至少一个多空蒙板
        # return：=====
            :rtype: object: 一个混合后的多空蒙板
        """
        blndr = self.__timing_blender  # 从对象的属性中读取择时混合参数
        assert type(blndr) is str, 'Parmameter Type Error: the timing blender should be a text string!'
        # print 'timing blender is:', blndr
        l_m = 0
        for msk in ls_masks:  # 计算所有多空模版的和
            l_m += msk
        if blndr[0:3] == 'chg':  # 出现N个状态变化信号时状态变化
            # TODO: ！！本混合方法暂未完成！！
            # chg-N方式下，持仓仅有两个位置，1或0，持仓位置与各个蒙板的状态变化有关，如果当前状态为空头，只要有N个或更多
            # 蒙板空转多，则结果转换为多头，反之亦然。这种方式与pos-N的区别在于，pos-N在多转空时往往滞后，因为要满足剩余
            # 的空头数量小于N后才会转空头，而chg-N则不然。例如，三个组合策略下pos-1要等至少两个策略多转空后才会转空，而
            # chg-1只要有一个策略多转空后，就会立即转空
            # 已经实现的chg-1方法由pandas实现，效率很低
            # print 'the first long/short mask is\n', ls_masks[-1]
            assert isinstance(l_m, np.ndarray), 'TypeError: the long short position mask should be an ndArray'
            return np.apply_along_axis(_timing_blend_change, 1, l_m)
        else:  # 另外两种混合方式都需要用到蒙板累加，因此一同处理
            l_count = len(ls_masks)
            # print 'the first long/short mask is\n', ls_masks[-1]
            if blndr == 'cumulate':
                # cumulate方式下，持仓取决于看多的蒙板的数量，看多蒙板越多，持仓越高，只有所有蒙板均看空时，最终结果才看空
                # 所有蒙板的权重相同，因此，如果一共五个蒙板三个看多两个看空时，持仓为60%
                # print 'long short masks are merged by', blndr, 'result as\n', l_m / l_count
                return l_m / l_count
            elif blndr[0:3] == 'pos':
                # pos-N方式下，持仓同样取决于看多的蒙板的数量，但是持仓只能为1或0，只有满足N个或更多蒙板看多时，最终结果
                # 看多，否则看空，如pos-2方式下，至少两个蒙板看多则最终看多，否则看空
                # print 'timing blender mode: ', blndr
                n = int(blndr[-1])
                # print 'long short masks are merged by', blndr, 'result as\n', l_m.clip(n - 1, n) - (n - 1)
                return l_m.clip(n - 1, n) - (n - 1)
            else:
                print('Blender text not recognized!')
        pass

    def __selecting_blend(self, sel_masks):
        #
        exp = self.__selecting_blender[:]
        # print('expression in operation module', exp)
        s = []
        while exp:  # previously: while exp != []
            if exp[-1].isdigit():
                s.append(sel_masks[int(exp.pop())])
            else:
                s.append(_blend(s.pop(), s.pop(), exp.pop()))
        return unify(s[0])

    def __ricon_blend(self, ricon_mats):
        if self.__ricon_blender == 'add':
            r_m = ricon_mats.pop()
            while ricon_mats:  # previously while ricon_mats != []
                r_m += ricon_mats.pop()
            return r_m

    @property
    def _exp_to_blender(self):
        """选股策略混合表达式解析程序，将通常的中缀表达式解析为前缀运算队列，从而便于混合程序直接调用

        系统接受的合法表达式为包含 '*' 与 '+' 的中缀表达式，符合人类的思维习惯，使用括号来实现强制
        优先计算，如 '0 + (1 + 2) * 3'; 表达式中的数字0～3代表选股策略列表中的不同策略的索引号
        上述表达式虽然便于人类理解，但是不利于快速计算，因此需要转化为前缀表达式，其优势是没有括号
        按照顺序读取并直接计算，便于程序的运行。为了节省系统运行开销，在给出混合表达式的时候直接将它
        转化为前缀表达式的形式并直接存储在blender列表中，在混合时直接调用并计算即可
        input： =====
            no input parameter
        return：===== s2: 前缀表达式
            :rtype: list: 前缀表达式
        """
        #TODO: extract expression with re module
        prio = {'or': 0,
                'and': 1}
        # 定义两个队列作为操作堆栈
        s1 = []  # 运算符栈
        s2 = []  # 结果栈
        # 读取字符串并读取字符串中的各个元素（操作数和操作符），当前使用str对象的split()方法进行，要
        # 求字符串中个元素之间用空格或其他符号分割，应该考虑写一个self.__split()方法，不依赖空格对
        # 字符串进行分割
        # exp_list = self.__selecting_blender_string.split()
        exp_list = list(self.__selecting_blender_string)
        # 开始循环读取所有操作元素
        while exp_list:
            s = exp_list.pop()
            # 从右至左逐个读取表达式中的元素（数字或操作符）
            # 并按照以下算法处理
            if s.isdigit():
                # 1，如果元素是数字则压入结果栈
                s2.append(s)

            elif s == ')':
                # 2，如果元素是反括号则压入运算符栈
                s1.append(s)
            elif s == '(':
                # 3，扫描到（时，依次弹出所有运算符直到遇到），并把该）弹出
                while s1[-1] != ')':
                    s2.append(s1.pop())
                s1.pop()
            elif s in prio.keys():
                # 4，扫描到运算符时：
                if s1 == [] or s1[-1] == ')' or prio[s] >= prio[s1[-1]]:
                    # 如果这三种情况则直接入栈
                    s1.append(s)
                else:
                    # 否则就弹出s1中的符号压入s2，并将元素放回队列
                    s2.append(s1.pop())
                    exp_list.append(s)
        while s1:
            s2.append(s1.pop())
        s2.reverse()  # 表达式解析完成，生成前缀表达式
        return s2
