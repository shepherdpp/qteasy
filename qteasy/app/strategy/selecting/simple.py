# coding=utf-8
class Selecting_Simple(Selecting):
    '基础选股策略：保持历史股票池中的所有股票都被选中，投资比例平均分配'
    _stg_name = 'SIMPLE SELECTING'
    _stg_text = 'Selecting all share and distribute weights evenly'

    def _select(self, shares, date, pct):
        # 所有股票全部被选中，投资比例平均分配
        return [1. / len(shares)] * len(shares)