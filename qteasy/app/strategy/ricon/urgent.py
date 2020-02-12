# coding=utf-8
class Ricon_Urgent(Ricon):
    '''urgent风控类，继承自Ricon类，重写_generate_ricon方法'''
    # 跌幅控制策略，当N日跌幅超过p%的时候，强制生成卖出信号
    _par_count = 2
    _par_types = ['discr', 'conti']
    _par_bounds_or_enums = [(1, 40), (-0.5, 0.5)]
    _stg_name = 'URGENT'
    _stg_text = 'Generate selling signal when N-day drop rate reaches target'

    def generate(self, hist_price):
        # TODO 临时借用Ricon None策略的输出，应该改为正确的输出
        assert not self._pars is None, 'Parameter of Risk Control-Urgent should be a pair of numbers like (N, pct)\nN as days, pct as percent drop'
        assert type(hist_price) is np.ndarray, 'Type Error: input historical data should be ndarray'
        day, drop = self._pars

        diff = (hist_price - np.roll(hist_price, day)) / hist_price
        return np.where(diff < drop, -1, 0)