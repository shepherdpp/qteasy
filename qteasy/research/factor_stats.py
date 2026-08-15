# coding=utf-8
# ======================================
# File:     factor_stats.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-08-15
# Desc:
#   因子研究统计：截面 IC 与 IC 摘要（非回测）。
# ======================================

import numpy as np
import pandas as pd

from qteasy.history import HistoryPanel


def factor_ic(
        panel: HistoryPanel,
        factor_htype: str,
        return_htype: str,
        *,
        method: str = 'spearman',
        min_assets: int = 2,
) -> pd.Series:
    """计算逐期截面因子 IC（Information Coefficient）。

    每个交易日在 share 维上对 ``factor_htype`` 与 ``return_htype`` 两列做相关；
    **不会**在函数内对收益列做 ``shift``——前瞻收益须由调用方事先构造并写入面板。
    本函数面向研究粗验，**不是** Backtester。

    Parameters
    ----------
    panel : HistoryPanel
        至少包含因子列与收益列的面板。
    factor_htype : str
        因子列名（须已在 ``panel.htypes`` 中）。
    return_htype : str
        收益列名（须已对齐到当期；含前瞻收益时由调用方先 ``shift``）。
    method : {'spearman', 'pearson'}, default 'spearman'
        截面相关系数方法。
    min_assets : int, default 2
        某日两侧均非 NaN 的有效标的数低于该阈值时，该日 IC 为 NaN；须 ``>= 2``。

    Returns
    -------
    pandas.Series
        index 为 ``hdates``，值为逐期 IC，``name='ic'``；空面板返回长度为 0 的 Series。

    Raises
    ------
    ValueError
        未知列名、非法 ``method`` / ``min_assets``。

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> from qteasy import HistoryPanel
    >>> from qteasy.research import factor_ic
    >>> data = np.array([[[1., 2.], [3., 1.]],
    ...                  [[2., 4.], [2., 2.]],
    ...                  [[3., 6.], [1., 3.]]])
    >>> hp = HistoryPanel(data, levels=['a', 'b', 'c'],
    ...                   rows=pd.date_range('2020-01-01', periods=2),
    ...                   columns=['factor', 'ret'])
    >>> factor_ic(hp, 'factor', 'ret', method='pearson').iloc[0]
    1.0
    """
    if panel.is_empty:
        return pd.Series(dtype=float, name='ic')
    if method not in ('spearman', 'pearson'):
        raise ValueError(
            f"method must be 'spearman' or 'pearson', got {method!r}"
        )
    if not isinstance(min_assets, (int, np.integer)) or isinstance(min_assets, bool):
        raise ValueError(f'min_assets must be an int >= 2, got {min_assets!r}')
    if int(min_assets) < 2:
        raise ValueError(f'min_assets must be >= 2, got {min_assets}')
    min_assets_i = int(min_assets)

    if factor_htype not in panel.htypes:
        raise ValueError(f"Unknown factor_htype {factor_htype!r}")
    if return_htype not in panel.htypes:
        raise ValueError(f"Unknown return_htype {return_htype!r}")

    fi = panel.htypes.index(factor_htype)
    ri = panel.htypes.index(return_htype)
    # values: (shares, dates, htypes)
    factor_2d = np.asarray(panel.values[:, :, fi], dtype=float)
    return_2d = np.asarray(panel.values[:, :, ri], dtype=float)
    hdates = list(panel.hdates)
    n_dates = factor_2d.shape[1]

    ics = np.full(n_dates, np.nan, dtype=float)
    for t in range(n_dates):
        f = pd.Series(factor_2d[:, t])
        r = pd.Series(return_2d[:, t])
        mask = f.notna() & r.notna()
        if int(mask.sum()) < min_assets_i:
            continue
        ics[t] = float(f[mask].corr(r[mask], method=method))

    return pd.Series(ics, index=hdates, name='ic', dtype=float)


def factor_ic_summary(ic: pd.Series) -> pd.Series:
    """对 IC 时序做标量摘要：均值、标准差、IR 与胜率。

    Parameters
    ----------
    ic : pandas.Series
        逐期 IC（通常为 ``factor_ic`` 的返回值）。

    Returns
    -------
    pandas.Series
        index 为 ``mean`` / ``std`` / ``ir`` / ``win_rate``。
        ``ir = mean / std``（样本标准差 ``ddof=1``）；``std`` 为 0 或有效样本不足时 ``ir`` 为 NaN。
        ``win_rate`` 为 ``ic > 0`` 占比（分母为非 NaN 期数）；无有效样本时为 NaN。

    Examples
    --------
    >>> import pandas as pd
    >>> from qteasy.research import factor_ic_summary
    >>> factor_ic_summary(pd.Series([1.0, -1.0])).loc['mean']
    0.0
    """
    if not isinstance(ic, pd.Series):
        raise TypeError(f'ic must be a pandas.Series, got {type(ic)}')

    keys = ['mean', 'std', 'ir', 'win_rate']
    if len(ic) == 0:
        return pd.Series({k: np.nan for k in keys}, dtype=float)

    valid = ic.dropna()
    if len(valid) == 0:
        return pd.Series({k: np.nan for k in keys}, dtype=float)

    mean_v = float(valid.mean())
    std_v = float(valid.std(ddof=1)) if len(valid) >= 2 else np.nan
    if std_v is None or (isinstance(std_v, float) and (np.isnan(std_v) or std_v == 0.0)):
        ir_v = np.nan
    else:
        ir_v = mean_v / std_v
    win_rate = float((valid > 0).sum() / len(valid))

    return pd.Series(
        {'mean': mean_v, 'std': std_v, 'ir': ir_v, 'win_rate': win_rate},
        dtype=float,
    )
