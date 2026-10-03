# coding=utf-8
# ======================================
# File: test_run_cancel.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-09-27
# Desc:
# 回测 / 优化 / refill 在 cancel_check 为真时于下一步停住。
# ======================================

import unittest
from types import SimpleNamespace

import numpy as np

from qteasy.backtest import backtest_batch_steps
from qteasy.cancel_check import RunCancelled, bind_cancel_check, reset_cancel_check
from qteasy.core import refill_data_source
from qteasy.database import DataSource
from qteasy.optimization import Optimizer


class _QuietSource(DataSource):
    """不建文件库，只记录是否写表。"""

    def __init__(self) -> None:
        self.writes = []
        self.connection_type = "quiet"

    def get_table_info(self, table, print_info=False):
        print(" table info:", table)
        return {"pk_max1": "20990101"}

    def update_table_data(self, table, df, merge_type="update"):
        print(" wrote table:", table, "rows:", len(df))
        self.writes.append(table)
        return len(df)


class TestRunCancel(unittest.TestCase):
    """协作式取消停在循环边界。"""

    def test_backtest_batch_steps_stops_before_first_signal(self) -> None:
        """cancel_check 一开始为真时，不改持仓现金。"""

        print("\n[TestRunCancel] backtest stops before first signal")
        signal_count = 2
        share_count = 1
        own_cashes = np.zeros(signal_count + 1, dtype=float)
        with self.assertRaises(RunCancelled):
            backtest_batch_steps(
                signal_types=np.zeros(signal_count, dtype=int),
                op_signals=np.zeros((signal_count, share_count), dtype=float),
                cash_investment_array=np.array([1000.0, 500.0]),
                cash_inflation_array=np.ones(signal_count, dtype=float),
                delivery_day_indicators=np.ones(signal_count, dtype=int),
                own_cashes=own_cashes,
                own_amounts_array=np.zeros((signal_count + 1, share_count), dtype=float),
                available_cashes=np.zeros(signal_count + 1, dtype=float),
                available_amounts_array=np.zeros((signal_count + 1, share_count), dtype=float),
                trade_prices=np.full((signal_count, share_count), 10.0),
                trade_records_array=np.zeros((signal_count, share_count), dtype=float),
                trade_cost_array=np.zeros((signal_count, share_count), dtype=float),
                cost_params=np.array([0.0, 0.0, 0.0, 0.0, 0.0]),
                pt_buy_threshold=0.0,
                pt_sell_threshold=0.0,
                long_pos_limit=1.0,
                short_pos_limit=-1.0,
                allow_sell_short=False,
                moq_buy=0.0,
                moq_sell=0.0,
                cash_delivery_period=0,
                stock_delivery_period=0,
                cancel_check=lambda: True,
            )
        print(" own_cashes:", own_cashes.tolist())
        self.assertEqual(own_cashes.tolist(), [0.0, 0.0, 0.0])

    def test_optimize_sequential_stops_before_next_parameter(self) -> None:
        """已评估一个参数后，下一个参数不再开始。"""

        print("\n[TestRunCancel] optimize stops before next parameter")
        calls = []

        class _Host:
            running_backtester = SimpleNamespace(clear_backtest_buffers=lambda: None)

            def _evaluate_parameter(self, par):
                calls.append(par)
                print(" evaluated:", par)
                return 0.2

            def _deep_evaluate_parameter(self, par):
                return 0.2, {}

        pool = SimpleNamespace(push=lambda **kwargs: None)
        token = bind_cancel_check(lambda: len(calls) >= 1)
        try:
            with self.assertRaises(RunCancelled):
                Optimizer._evaluate_parameters_sequential(
                    _Host(),
                    total=3,
                    par_value_list=[1, 2, 3],
                    result_pool=pool,
                    epoch_str="t",
                    deep_eval=False,
                    leave_progress_bar=False,
                )
        finally:
            reset_cancel_check(token)
        print(" calls:", calls)
        self.assertEqual(calls, [1])

    def test_refill_returns_before_writing_when_cancel_check_is_set(self) -> None:
        """取消在进入表循环时为真，则不写数据源。"""

        print("\n[TestRunCancel] refill stops before download")
        source = _QuietSource()
        refill_data_source(
            tables="stock_basic",
            data_source=source,
            channel="tushare",
            cancel_check=lambda: True,
            parallel=False,
            refill_dependent_tables=False,
            refresh_trade_calendar=False,
        )
        print(" writes:", source.writes)
        self.assertEqual(source.writes, [])


if __name__ == "__main__":
    unittest.main()
