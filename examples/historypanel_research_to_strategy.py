# coding=utf-8
# ======================================
# File: historypanel_research_to_strategy.py
# Author: Jackie PENG / qteasy
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-03
# Desc:
#   演示：在合成 HistoryPanel 上做动量因子研究，并给出与之一致的 FactorSorter 骨架
#   （正式回测需配置 Operator + qt.run，见教程 2.5 §9）。
# ======================================
from __future__ import annotations

import numpy as np
import pandas as pd

import qteasy as qt
from qteasy import StgData
from qteasy.history import HistoryPanel


class Mom5Factor(qt.FactorSorter):
    """5 期简单动量：与 HP 上 ``returns(..., periods=5, as_panel=True)`` 的经济含义一致。"""

    def __init__(self) -> None:
        super().__init__(
            name='Mom5',
            description='5-bar simple momentum on daily close',
            data_types=[StgData('close', freq='d', asset_type='E')],
            window_length=6,
            max_sel_count=2,
            sort_ascending=False,
            condition='any',
            use_latest_data_cycle=True,
        )

    def realize(self):
        close_w = self.get_data('close_E_d')
        out = close_w[-1] / close_w[0] - 1.0
        out = np.where(np.isfinite(out), out, np.nan)
        return out


def main() -> None:
    print('\n[historypanel_research_to_strategy] 合成面板：3 标的 × 30 日 × close')
    rows = pd.date_range('2020-01-01', periods=30, freq='D')
    rng = np.random.default_rng(0)
    prices = 10.0 + np.cumsum(rng.standard_normal((3, 30)), axis=1)
    hp = HistoryPanel(
        values=prices.reshape(3, 30, 1),
        levels=['S0', 'S1', 'S2'],
        rows=rows,
        columns=['close'],
    )
    hp_mom = hp.returns(price_htype='close', periods=5, method='simple', as_panel=True)
    hp_rank = hp_mom.rank(by='ret_close')
    ri = hp_rank.htypes.index('rank_ret_close')
    print('  最后交易日截面 rank(ret_close):', hp_rank.values[:, -1, ri])

    print('\n[historypanel_research_to_strategy] FactorSorter 骨架（需加入 Operator 后 realize 才有数据）')
    stg = Mom5Factor()
    print('  name:', stg.name)
    print('  data_type ids:', list(stg.data_types.keys()))
    print('  window_lengths:', dict(stg.window_lengths))


if __name__ == '__main__':
    main()
