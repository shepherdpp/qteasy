# coding=utf-8
class Timing_Crossline(Timing):
    '''crossline择时策略类，利用长短均线的交叉确定多空状态

        crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型

    '''
    # 重写策略参数相关信息
    _par_count = 4
    _par_types = ['discr', 'discr', 'conti', 'enum']
    _par_bounds_or_enums = [(10, 250), (10, 250), (10, 250), ('buy', 'sell')]
    _stg_name = 'CROSSLINE STRATEGY'
    _stg_text = 'Moving average crossline strategy, determin long/short position according to the cross point of long and short term moving average prices'

    def _generate_one(self, hist_price, params):
        '''crossline策略使用四个参数：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型'''
        s, l, m, hesitate = params
        # 计算均线前排除所有的无效值，无效值前后价格处理为连续价格，返回时使用pd.Series重新填充日期序列恢复
        # 去掉的无效值
        # print 'Generating Crossline Long short Mask with parameters', params
        drop = ~np.isnan(hist_price)
        cat = np.zeros_like(hist_price)
        h_ = hist_price[drop]  # 仅针对非nan值计算，忽略股票停牌时期
        # 计算长短均线之间的距离
        diff = self._ma(h_, l) - self._ma(h_, s)
        # TODO: 可以改成np.digitize()来完成，效率更高 -- 测试结果表明np.digitize速度甚至稍慢于两个where
        cat[drop] = np.where(diff < -m, 1, np.where(diff >= m, -1, 0))
        # TODO: 处理hesitate参数 &&&未完成代码&&&
        if hesitate == 'buy':
            pass
        elif hesitate == 'sell':
            pass
        else:
            pass
        # 重新恢复nan值可以使用pd.Series也可以使用pd.reindex，可以测试哪一个速度更快，选择速度更快的一个
        return cat  # 返回时填充日期序列恢复无效值