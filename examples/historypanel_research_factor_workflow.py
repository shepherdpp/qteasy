# coding=utf-8
# ======================================
# File: historypanel_research_factor_workflow.py
# Author: Jackie PENG / qteasy
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-08-16
# Desc:
#   演示：合成 HistoryPanel → 自备前瞻收益 → qteasy.research
#   （factor_ic / 分位组合 / 多空）与 HistoryPanel.corr（时序矩阵）。
#   无网络依赖；非 Backtester。教程见 2.5「截面 IC 与分位组合」。
# ======================================
from __future__ import annotations

import numpy as np
import pandas as pd

from qteasy.history import HistoryPanel
from qteasy.research import (
    factor_ic,
    factor_ic_summary,
    long_short_return,
    quantile_portfolio,
)


def main() -> None:
    print('\n[historypanel_research_factor_workflow] 合成面板 M=6,L=12（factor + fwd_ret）')
    rng = np.random.default_rng(42)
    n_shares, n_dates = 6, 12
    rows = pd.date_range('2020-01-01', periods=n_dates, freq='D')
    shares = [f'S{i}' for i in range(n_shares)]

    # 截面上因子与下一期收益略正相关（研究示意，非投资建议）
    factor = rng.standard_normal((n_shares, n_dates))
    noise = rng.standard_normal((n_shares, n_dates)) * 0.5
    # fwd_ret[t] ≈ 与 factor[t] 同向 + 噪声（已对齐到当期，不在 research 内 shift）
    fwd_ret = 0.02 * factor + 0.01 * noise

    hp = HistoryPanel(
        values=np.stack([factor, fwd_ret], axis=2),
        levels=shares,
        rows=rows,
        columns=['factor', 'fwd_ret'],
    )
    print('  shape:', hp.shape, 'htypes:', hp.htypes)

    ic = factor_ic(hp, 'factor', 'fwd_ret', method='spearman')
    summary = factor_ic_summary(ic)
    print('\n[IC] spearman series (head):')
    print(ic.head())
    print('[IC] summary:')
    print(summary)

    qret = quantile_portfolio(hp, 'factor', 'fwd_ret', n_quantiles=3)
    ls = long_short_return(qret, long='Q3', short='Q1')
    print('\n[Quantile] mean by bucket:')
    print(qret.mean())
    print('[Long-short Q3-Q1] mean:', float(ls.mean()))
    print('[Long-short] head:')
    print(ls.head())

    corr_m = hp.corr('factor')
    print('\n[corr] shares×shares 时序相关矩阵（与逐日截面 IC 语义不同）')
    print('  shape:', corr_m.shape)
    print('  diagonal sample:', [float(corr_m.loc[s, s]) for s in shares[:3]])
    print(corr_m.round(3))


if __name__ == '__main__':
    main()
