# coding=utf-8
# ======================================
# File:     hp_plot_minimal.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-03-13
# Desc:
#   Minimal example: HistoryPanel.plot() as the single entry for visualization.
#   Uses only existing data in the panel (no computation); chart types are chosen by htypes.
# ======================================

"""
Minimal example: HistoryPanel visualization with hp.plot()

Run from project root (with qteasy installed or PYTHONPATH=.):
  python examples/hp_plot_minimal.py

Or in Notebook:
  from examples.hp_plot_minimal import run_example
  fig = run_example()
"""

import sys
from pathlib import Path

if __name__ == '__main__' and (Path(__file__).resolve().parent.parent / 'qteasy').is_dir():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd


def run_example():
    """Build a small HistoryPanel and call hp.plot(); return the figure."""
    from qteasy.history import HistoryPanel

    n_dates = 30
    n_shares = 2
    htypes = ['open', 'high', 'low', 'close', 'vol']
    n_htypes = len(htypes)
    np.random.seed(42)
    values = np.random.randn(n_shares, n_dates, n_htypes).cumsum(axis=1) + 100
    values[:, :, 1] = values[:, :, 3] + np.random.randn(n_shares, n_dates) * 0.5
    values[:, :, 0] = values[:, :, 3] - np.abs(np.random.randn(n_shares, n_dates)) * 0.5
    values[:, :, 4] = np.abs(np.random.randn(n_shares, n_dates)) * 1e6
    shares = ['000001.SZ', '000002.SZ']
    rows = pd.date_range('2024-01-01', periods=n_dates, freq='B')
    hp = HistoryPanel(values=values, levels=shares, rows=rows, columns=htypes)
    fig = hp.plot(layout='stack')
    return fig


if __name__ == '__main__':
    fig = run_example()
    print('Figure created with', len(fig.axes), 'axes.')
    fig.savefig('hp_plot_minimal_out.png', dpi=100, bbox_inches='tight')
    print('Saved to hp_plot_minimal_out.png')
