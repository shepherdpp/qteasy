# coding=utf-8
class Timing_DMA(Timing):
    'DMA择时策略，继承自Timing类，重写_generate方法'
    _par_count = 3
    _par_types = ['discr', 'discr', 'discr']
    _par_bounds_or_enums = [(10, 250), (10, 250), (10, 250)]
    _stg_name = 'quick-DMA STRATEGY'
    _stg_text = 'numpy based DMA strategy, determin long/short position according to differences of moving average prices'

    def _generate_one(self, hist_price, params):
        # 使用基于numpy的移动平均计算函数的快速DMA择时方法
        s, l, d = params
        #print 'Generating Quick DMA Long short Mask with parameters', params
        drop = ~np.isnan(hist_price)
        cat = np.zeros_like(hist_price)
        h_ = hist_price[drop]
        # 计算指数的移动平均价格
        DMA = self._ma(h_, s) - self._ma(h_, l)
        AMA = DMA.copy()
        AMA[~np.isnan(DMA)] = self._ma(DMA[~np.isnan(DMA)], d)
        #print('qDMA generated DMA and AMA signal:', DMA.size, DMA, '\n', AMA.size, AMA)
        # 生成DMA多空判断：
        # 1， DMA在AMA上方时，多头区间，即DMA线自下而上穿越AMA线, signal = -1
        # 2， DMA在AMA下方时，空头区间，即DMA线自上而下穿越AMA线
        # 3， DMA与股价发生背离时的交叉信号，可信度较高
        cat[drop] = np.where(DMA > AMA, 1, 0)
        #print('qDMA generate category data with as type', cat.size, cat)
        return cat