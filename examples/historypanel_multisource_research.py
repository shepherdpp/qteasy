# coding=utf-8
# ======================================
# File: historypanel_multisource_research.py
# Author: Jackie PENG / qteasy
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-03
# Desc:
#   演示：两块合成 HistoryPanel（价格 / “估值”）经 align_to 对齐后 assign 合并，
#   再做截面 zscore（教程 2.5 §10）。真实场景请用 get_history_data 替换合成数据。
# ======================================
from __future__ import annotations

import numpy as np
import pandas as pd

from qteasy.history import HistoryPanel


def main() -> None:
    print('\n[historypanel_multisource_research] 同构 htypes（close,pb）两板，日期错开一日后 align_to')
    rows_a = pd.date_range('2020-01-01', periods=8, freq='D')
    rows_b = pd.date_range('2020-01-02', periods=8, freq='D')
    rng = np.random.default_rng(1)
    close = 10.0 + np.cumsum(rng.standard_normal((2, 8)), axis=1)
    pb = np.abs(rng.random((2, 8))) + 0.5

    nan_close = np.full_like(close, np.nan)
    nan_pb = np.full_like(pb, np.nan)
    hp_px = HistoryPanel(
        values=np.stack([close, nan_pb], axis=2),
        levels=['A', 'B'],
        rows=rows_a,
        columns=['close', 'pb'],
    )
    hp_pb = HistoryPanel(
        values=np.stack([nan_close, pb], axis=2),
        levels=['A', 'B'],
        rows=rows_b,
        columns=['close', 'pb'],
    )

    a, b = hp_px.align_to(hp_pb, join='inner')
    print('  inner 对齐后 L =', a.shape[1], '（共同交易日）')

    pb_vals = b['pb'].values[:, :, 0]
    close_vals = a['close'].values[:, :, 0]
    hp_joined = a.assign(
        close=lambda p: close_vals,
        pb=lambda p: pb_vals,
    )
    hp_joined = hp_joined.assign(
        inv_pb=lambda p: 1.0 / np.maximum(p['pb'].values[:, :, 0], 1e-6),
    )
    hp_z = hp_joined.zscore(by='inv_pb', method='cs')
    print('  合并后 htypes:', hp_joined.htypes)
    print('  zscore 列:', [h for h in hp_z.htypes if h.startswith('cs_z')][-1])
    zi = hp_z.htypes.index('cs_z_inv_pb')
    print('  最后一日截面 z（inv_pb）:', hp_z.values[:, -1, zi])


if __name__ == '__main__':
    main()
