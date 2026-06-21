# coding=utf-8
# ======================================
# File: historypanel_basic_plot.py
# Author: Jackie PENG / qteasy
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-05-31
# Desc:
#   HistoryPanel 基础可视化：对应教程 2.0「从 DataFrame 到 HistoryPanel」桥接
#   与 2.5 §1 准备数据。
# ======================================
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import qteasy as qt


def main() -> None:
    """HistoryPanel 基础可视化示例。

    本示例展示：
    1. 使用 get_history_data 获取单标的 OHLCV 数据（返回 HistoryPanel）；
    2. 在 HistoryPanel 上绘制静态 K 线 + 成交量；
    3. 在支持的环境下绘制交互式 K 线；
    4. 演示简单的 highlight 配置。
    """
    print('\n[historypanel_basic_plot] 获取 000300.SH 日线 OHLCV → HistoryPanel')
    hp = qt.get_kline(
        shares='000300.SH',
        start='20230101',
        end='20231231',
        freq='d',
        as_panel=True,
    )
    print('  shape:', hp.shape)
    print('  shares:', hp.shares)
    print('  htypes:', hp.htypes)

    print('\n[historypanel_basic_plot] 静态 K 线 + 成交量')
    hp.plot(interactive=False)

    print('\n[historypanel_basic_plot] 交互式 K 线（需 plotly / ipywidgets）')
    hp.plot(interactive=True)

    print('\n[historypanel_basic_plot] highlight=max（收盘价最大值）')
    hp.plot(
        interactive=True,
        highlight={'condition': 'max'},
    )


if __name__ == '__main__':
    main()
