# coding=utf-8
class Selecting_Trend(Selecting):
    '趋势选股策略，继承自选股策略类'
    _stg_name = 'TREND SELECTING'
    _stg_text = 'Selecting share according to detected trends'

    def _select(self, shares, date, pct):
        # 所有股票全部被选中，权值（投资比例）平均分配
        return [1. / len(shares)] * len(shares)

    pass