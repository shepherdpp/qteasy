# coding=utf-8
# ======================================
# File: data_playground_e2e.py
# Author: Jackie PENG / qteasy
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-06-17
# Desc:
#   S1.2 数据体验最小闭环：配置好本地数据源后，取多标的 K 线 → 预设出图 →
#   收益/截面 zscore → 研究向组合与 benchmark 对比。对应教程 2.0 最小数据集 + 2.5 §0。
# ======================================
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

# 从仓库根目录运行示例时保证可 import 本地 qteasy 包
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import qteasy as qt


# 与教程 2.0「最小数据集」及 2.5 §0 一致
STOCK_POOL: List[str] = [
    '000001.SZ',
    '600519.SH',
    '300750.SZ',
]
BENCHMARK: str = '000300.SH'
START: str = '20220101'
END: str = '20221231'


def _ensure_local_data_hint() -> None:
    """检查本地是否已有教程所需日线数据；缺失时给出英文指引后退出。"""
    print('\n[data_playground_e2e] 检查本地数据源（probe get_kline on benchmark）')
    try:
        probe = qt.get_kline(
            shares=BENCHMARK,
            start=START,
            end='20220110',
            freq='d',
            as_panel=True,
        )
        bar_count = probe.shape[1]
        print('  probe bars for', BENCHMARK, 'on', START, ':', bar_count)
        if bar_count < 1:
            _raise_missing_data()
    except Exception as exc:
        print('  probe failed:', type(exc).__name__, exc)
        _raise_missing_data()


def _raise_missing_data() -> None:
    msg = (
        'Local OHLCV data not found. Please run tutorial 2.0 refill first, e.g.:\n'
        "  qt.refill_data_source(tables='trade_calendar, stock_basic, index_basic')\n"
        "  qt.refill_data_source(tables='index_daily', symbols='000300.SH', "
        f"start_date='{START}', end_date='{END}')\n"
        "  qt.refill_data_source(tables='stock_daily', symbols='000001.SZ,600519.SH,300750.SZ', "
        f"start_date='{START}', end_date='{END}')"
    )
    raise RuntimeError(msg)


def demo_data_playground(
        stocks: List[str] | None = None,
        benchmark: str = BENCHMARK,
        start: str = START,
        end: str = END,
        *,
        check_local: bool = True,
        plot: bool = True,
) -> Dict[str, Any]:
    """运行「玩数据」最小闭环（研究向，非回测）。

    Parameters
    ----------
    stocks : list of str, optional
        个股代码列表；默认使用教程示例池。
    benchmark : str
        基准指数代码，默认沪深 300。
    start, end : str
        日期区间 YYYYMMDD。
    check_local : bool
        是否在取数前检查本地表概览。
    plot : bool
        是否调用 ``hp.plot``（静态图）；无 GUI 环境可设 False。

    Returns
    -------
    dict
        含 ``hp``、``hp_preset``、``hp_z``、``pf`` 等中间对象。
    """
    if stocks is None:
        stocks = list(STOCK_POOL)

    if check_local:
        _ensure_local_data_hint()

    shares = stocks + [benchmark]
    print('\n[data_playground_e2e] 1) get_kline → HistoryPanel')
    print('  shares:', shares)
    hp = qt.get_kline(
        shares=shares,
        start=start,
        end=end,
        freq='d',
        as_panel=True,
    )
    m, length, n = hp.shape
    print('  hp.shape:', hp.shape)
    print('  htypes:', hp.htypes)
    if length < 20:
        raise RuntimeError(
            f'HistoryPanel has only {length} bars; widen date range or refill local data.'
        )

    print('\n[data_playground_e2e] 2) research_preset + plot')
    hp_preset = hp.research_preset('ohlcv_macd_ma', inplace=False)
    print('  preset htypes (tail):', hp_preset.htypes[-6:])
    if plot:
        hp_preset.plot(interactive=False)

    print('\n[data_playground_e2e] 3) returns + cross-sectional zscore')
    hp_ret = hp.returns(price_htype='close', periods=5, method='simple', as_panel=True)
    hp_z = hp_ret.zscore(by='ret_close', method='cs')
    z_col = [h for h in hp_z.htypes if h.startswith('cs_z')][-1]
    zi = hp_z.htypes.index(z_col)
    last_z = hp_z.values[:, -1, zi]
    print('  zscore column:', z_col)
    print('  last-day cross-section z (by share order):', last_z)

    print('\n[data_playground_e2e] 4) research portfolio vs benchmark (not backtest)')
    pf = hp.portfolio(
        htypes='close',
        mode='equal',
        benchmark=benchmark,
        benchmark_output='tag_along',
        new_share_name='EW',
    )
    print('  portfolio shares:', pf.shares)
    print(
        '  NOTE: portfolio/cum_return here are research-only; '
        'no fees, delivery, or MOQ — use Operator for formal backtest.'
    )

    return {
        'hp': hp,
        'hp_preset': hp_preset,
        'hp_ret': hp_ret,
        'hp_z': hp_z,
        'pf': pf,
    }


def main() -> None:
    print('\n[data_playground_e2e] S1.2 minimal data playground (tutorial 2.5 §0)')
    try:
        res = demo_data_playground(plot=False)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    print('\n[data_playground_e2e] done; keys:', list(res.keys()))


if __name__ == '__main__':
    main()
