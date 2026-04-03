# coding=utf-8
# ======================================
# File: historypanel_statsmodels_export.py
# Author: Jackie PENG / qteasy
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-03
# Desc:
#   演示：HistoryPanel → 长表 → 可选 statsmodels OLS（教程 2.5 §11）。
#   未安装 statsmodels 时跳过回归并打印提示。
# ======================================
from __future__ import annotations

import numpy as np
import pandas as pd

from qteasy.history import HistoryPanel


def panel_to_long_df(hp: HistoryPanel, value_cols: list[tuple[str, str]]) -> pd.DataFrame:
    """将若干 htype 列堆成长表。

    Parameters
    ----------
    hp : HistoryPanel
        源面板。
    value_cols : list of tuple
        ``(htype 名, 长表中的列名)``。

    Returns
    -------
    pandas.DataFrame
        含 ``date``、``share`` 及用户指定列。
    """
    records: list[dict] = []
    m, l, _ = hp.shape
    indices = {out: hp.htypes.index(ht) for ht, out in value_cols}
    for mi, sh in enumerate(hp.shares):
        for li, dt in enumerate(hp.hdates):
            row: dict = {'date': dt, 'share': sh}
            for ht, out in value_cols:
                row[out] = hp.values[mi, li, indices[out]]
            records.append(row)
    return pd.DataFrame(records)


def main() -> None:
    print('\n[historypanel_statsmodels_export] 合成面板 M=2,L=5，含 close 与 factor')
    rows = pd.date_range('2020-01-01', periods=5, freq='D')
    rng = np.random.default_rng(2)
    close = 10.0 + np.cumsum(rng.standard_normal((2, 5)), axis=1)
    fac = rng.standard_normal((2, 5))
    values = np.stack([close, fac], axis=2)
    hp = HistoryPanel(
        values=values,
        levels=['X', 'Y'],
        rows=rows,
        columns=['close', 'factor'],
    )

    df_long = panel_to_long_df(hp, [('close', 'close'), ('factor', 'factor')])
    print('  long shape:', df_long.shape)
    print(df_long.head(6))

    try:
        import statsmodels.api as sm
    except ImportError:
        print('\n[historypanel_statsmodels_export] statsmodels 未安装，跳过 OLS（pip install statsmodels）')
        return

    sub = df_long[df_long['date'] == df_long['date'].iloc[-1]].dropna()
    print('\n[historypanel_statsmodels_export] 最后一交易日截面 OLS（演示因变量，非投资建议）')
    y = sub['close'] / sub['close'].mean() - 1.0
    X = sm.add_constant(sub['factor'])
    model = sm.OLS(y, X, missing='drop').fit()
    print(model.summary())


if __name__ == '__main__':
    main()
