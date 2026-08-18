# coding=utf-8
# ======================================
# File:     factor_stats.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-08-15
# Desc:
#   因子研究统计：截面 IC、分位组合与多空收益（非回测）。
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


def _quantile_column_names(n_quantiles: int) -> list:
    """生成 Q1..Qn 列名列表。"""
    return [f'Q{i}' for i in range(1, n_quantiles + 1)]


def quantile_portfolio(
        panel: HistoryPanel,
        factor_htype: str,
        return_htype: str,
        *,
        n_quantiles: int = 5,
        weight: str = 'equal',
) -> pd.DataFrame:
    """按因子截面分位分桶，计算各桶等权逐期收益。

    因子从小到大：``Q1`` 为最低因子桶，``Qn`` 为最高因子桶。
    **不会**在函数内对收益列做 ``shift``——前瞻收益须由调用方事先构造。
    本函数面向研究粗验，**不是** Backtester。

    Parameters
    ----------
    panel : HistoryPanel
        至少包含因子列与收益列的面板。
    factor_htype : str
        因子列名。
    return_htype : str
        收益列名（须已对齐到当期）。
    n_quantiles : int, default 5
        分位桶数量，须 ``>= 2``。
    weight : {'equal'}, default 'equal'
        桶内权重；v1 仅支持等权。

    Returns
    -------
    pandas.DataFrame
        index 为 ``hdates``，columns 为 ``Q1..Qn``；空面板返回 0 行同列名表。
        当日有效标的数小于 ``n_quantiles`` 时该日全为 NaN。

    Raises
    ------
    ValueError
        未知列名、非法 ``n_quantiles`` / ``weight``。

    Examples
    --------
    >>> import numpy as np
    >>> import pandas as pd
    >>> from qteasy import HistoryPanel
    >>> from qteasy.research import quantile_portfolio
    >>> data = np.array([
    ...     [[1., 10.], [4., 1.]],
    ...     [[2., 20.], [3., 2.]],
    ...     [[3., 30.], [2., 3.]],
    ...     [[4., 40.], [1., 4.]],
    ... ])
    >>> hp = HistoryPanel(data, levels=['a', 'b', 'c', 'd'],
    ...                   rows=pd.date_range('2020-01-01', periods=2),
    ...                   columns=['factor', 'ret'])
    >>> quantile_portfolio(hp, 'factor', 'ret', n_quantiles=2).iloc[0]['Q1']
    15.0
    """
    if not isinstance(n_quantiles, (int, np.integer)) or isinstance(n_quantiles, bool):
        raise ValueError(f'n_quantiles must be an int >= 2, got {n_quantiles!r}')
    if int(n_quantiles) < 2:
        raise ValueError(f'n_quantiles must be >= 2, got {n_quantiles}')
    n_q = int(n_quantiles)
    if weight != 'equal':
        raise ValueError(f"weight must be 'equal' in v1, got {weight!r}")

    cols = _quantile_column_names(n_q)
    if panel.is_empty:
        return pd.DataFrame(columns=cols, dtype=float)

    if factor_htype not in panel.htypes:
        raise ValueError(f"Unknown factor_htype {factor_htype!r}")
    if return_htype not in panel.htypes:
        raise ValueError(f"Unknown return_htype {return_htype!r}")

    fi = panel.htypes.index(factor_htype)
    ri = panel.htypes.index(return_htype)
    factor_2d = np.asarray(panel.values[:, :, fi], dtype=float)
    return_2d = np.asarray(panel.values[:, :, ri], dtype=float)
    hdates = list(panel.hdates)
    n_dates = factor_2d.shape[1]

    rows = []
    for t in range(n_dates):
        f = pd.Series(factor_2d[:, t])
        r = pd.Series(return_2d[:, t])
        mask = f.notna() & r.notna()
        n_valid = int(mask.sum())
        if n_valid < n_q:
            rows.append({c: np.nan for c in cols})
            continue
        f_v = f[mask]
        r_v = r[mask]
        # 稳定秩避免并列导致 qcut 失败；秩越小因子越低 → Q1
        ranks = f_v.rank(method='first')
        buckets = pd.qcut(ranks, n_q, labels=cols)
        bucket_ret = r_v.groupby(buckets, observed=False).mean()
        row = {c: float(bucket_ret[c]) if c in bucket_ret.index and pd.notna(bucket_ret[c])
               else np.nan for c in cols}
        rows.append(row)

    return pd.DataFrame(rows, index=hdates, columns=cols, dtype=float)


def long_short_return(
        quantile_returns: pd.DataFrame,
        *,
        long: str = 'Q5',
        short: str = 'Q1',
) -> pd.Series:
    """由分位桶收益表构造多空收益序列 ``long - short``。

    Parameters
    ----------
    quantile_returns : pandas.DataFrame
        通常为 ``quantile_portfolio`` 的返回值，列名为 ``Q1..Qn``。
    long : str, default 'Q5'
        多头桶列名。
    short : str, default 'Q1'
        空头桶列名。

    Returns
    -------
    pandas.Series
        index 与输入对齐，``name='long_short'``。

    Raises
    ------
    ValueError
        缺少 ``long`` 或 ``short`` 列。

    Examples
    --------
    >>> import pandas as pd
    >>> from qteasy.research import long_short_return
    >>> df = pd.DataFrame({'Q1': [1.0], 'Q5': [3.0]})
    >>> float(long_short_return(df).iloc[0])
    2.0
    """
    if not isinstance(quantile_returns, pd.DataFrame):
        raise TypeError(
            f'quantile_returns must be a pandas.DataFrame, got {type(quantile_returns)}'
        )
    if long not in quantile_returns.columns:
        raise ValueError(f"Missing long column {long!r} in quantile_returns")
    if short not in quantile_returns.columns:
        raise ValueError(f"Missing short column {short!r} in quantile_returns")

    out = quantile_returns[long] - quantile_returns[short]
    out.name = 'long_short'
    return out
