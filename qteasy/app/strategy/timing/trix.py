# coding=utf-8
class Timing_TRIX(Timing):
    'TRIX择时策略，继承自Timing类，重写__generate方法'
    # 运用TRIX均线策略，在idx历史序列上生成交易信号
    # 注意！！！
    # 由于TRIX使用指数移动均线，由于此种均线的计算特性，在历史数据集的前sRange + mRange个工作日上生成的数据不可用
    # 例如，sRange + mRange = 157时，前157个工作日内产生的买卖点不正确，应忽略
    _par_count = 2
    _par_types = ['discr', 'discr']
    _par_bounds_or_enums = [(10, 250), (10, 250)]
    _stg_name = 'TRIX STRATEGY'
    _stg_text = 'TRIX strategy, determin long/short position according to triple exponential weighted moving average prices'

    def _generate_one(self, hist_price, params):
        '''# 参数:
        # idx: 指定的参考指数历史数据
        # sRange, 短均线参数，短均线的移动平均计算窗口宽度，单位为日
        # dRange, DIFF的移动平均线计算窗口宽度，用于区分短均线与长均线的“初次相交”和“彻底击穿”

        '''
        s, m = params
        cut = s + m
        # print 'Generating TRIX Long short Mask with parameters', params
        drop = ~np.isnan(hist_price)
        cat = np.zeros_like(hist_price)
        h_ = hist_price[drop]

        # 计算指数的指数移动平均价格
        TR = self._ema(self._ema(self._ema(h_, s), s), s)
        TRIX = (TR - np.roll(TR, 1)) / np.roll(TR, 1) * 100
        MATRIX = self._ma(TRIX, m)

        # 生成TRIX多空判断：
        # 1， TRIX位于MATRIX上方时，长期多头状态, signal = -1
        # 2， TRIX位于MATRIX下方时，长期空头状态, signal = 1
        cat[drop] = np.where(TRIX > MATRIX, 1, 0)
        cat[0: cut] = np.nan
        return cat  # 返回时填充日期序列恢复nan值