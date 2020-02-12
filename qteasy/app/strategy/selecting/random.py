# coding=utf-8
class Selecting_Random(Selecting):
    '基础选股策略：在每个历史分段中，按照指定的概率（p<1时）随机抽取若干股票，或随机抽取指定数量（p>1）的股票进入投资组合，投资比例平均分配'
    _stg_name = 'RANDOM SELECTING'
    _stg_text = 'Selecting share Randomly and distribute weights evenly'

    def _select(self, shares, date, par):
        if par < 1:
            # 给定参数小于1，按照概率随机抽取若干股票
            chosen = np.random.choice([1, 0], size = len(shares), p = [par, 1-par])
        elif par >= 1: # 给定参数大于1，抽取给定数量的股票
            choose_at = np.random.choice(len(shares), size = (int(par)), replace = False)
            chosen = np.zeros(len(shares))
            chosen[choose_at] = 1
        return chosen.astype('float') / chosen.sum() # 投资比例平均分配