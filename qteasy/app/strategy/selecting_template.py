# coding=utf-8

class Selecting(Strategy):
    '选股策略类的抽象基类，所有选股策略类都继承该类'
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
        seg_pos[1:-1] = np.searchsorted(dates, bnds)
        # 最后一个分隔位等于历史区间的总长度
        seg_pos[-1] = len(dates) - 1
        # print('Results check, selecting - segment creation, segments:', seg_pos)
        # 计算每个分段的长度
        seg_lens = (seg_pos - np.roll(seg_pos, 1))[1:]
        return seg_pos, seg_lens, len(seg_pos) - 1

    def generate(self, hist_price, dates, shares):
        # 生成历史价格序列的选股组合信号：将历史数据分成若干连续片段，在每一个片段中应用某种规则建立投资组合
        # 建立的投资组合形成选股组合蒙版，每行向量对应所有股票在当前时间点在整个投资组合中所占的比例
        # 输入：
        # hist_price：历史数据, DataFrame
        # sel_pars：选股参数，通常包含选股频率以及生成的投资组合中包含的股票数量或比例
        # 输出：=====sel_mask：选股蒙版，是一个与输入历史数据尺寸相同的ndarray，dtype为浮点数，取值范围在0～1之间
        #  矩阵中的取值代表股票在投资组合中所占的比例，0表示投资组合中没有该股票，1表示该股票占比100%
        # 获取参数
        freq = self._pars[0]
        poq = self._pars[1]
        # 获取完整的历史日期序列，并按照选股频率生成分段标记位，完整历史日期序列从参数获得，股票列表也从参数获得
        # dates = hist_price.index.values
        # print('SPEED TEST Selection module, Time of segmenting history')
        # %time self._seg_periods(dates, freq)
        assert type(hist_price) is np.ndarray, 'Type Error: input historical data should be ndarray'
        seg_pos, seg_lens, seg_count = self._seg_periods(dates, freq)
        # shares = hist_price.columns
        # 一个空的list对象用于存储生成的选股蒙版
        sel_mask = np.zeros(shape=(len(dates), len(shares)), order='C')
        seg_start = 0

        # 以下版本采用向量化计算代替之前的循环版本，但该版本甚至稍慢于之前的循环版本
        '''
        #print('Selecting, generate function, segment position seg_pos: ', seg_pos)
        #print('Selecting, generate function: shape of sel_mask', sel_mask.shape)
        shares_arr = [shares] * (seg_count + 1)
        poq_arr = [poq] * (seg_count + 1)
        sel_mask_per_seg = np.array(list(map(self._select, shares_arr, dates, poq_arr)), dtype = 'float')
        #print('Selecting, generate function:, sel_mask per segmeng:', sel_mask_per_seg)
        sel_mask_builder = sel_mask_per_seg - np.roll(sel_mask_per_seg, 1)
        #print('Selecting, generate function:, sel_mask builder:', sel_mask_builder)
        sel_mask_builder[0] = sel_mask_per_seg[0]
        #print('Selecting, generate function:, sel_mask builder:', sel_mask_builder)
        sel_mask[seg_pos,:] = sel_mask_builder
        #print('Selecting, generate function:, final sel_mask and its shape:', sel_mask.cumsum(0), sel_mask.cumsum(0).shape)
        return sel_mask.cumsum(0)'''

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