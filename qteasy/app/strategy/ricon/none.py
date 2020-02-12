# coding=utf-8
class Ricon_None(Ricon):
    '''无风险控制策略，不对任何风险进行控制'''
    _stg_name = 'NONE'
    _stg_text = 'Do not take any risk control activity'

    def generate(self, hist_price):
        return np.zeros_like(hist_price)