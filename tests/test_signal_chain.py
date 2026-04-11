# coding=utf-8
# ======================================
# File:     test_signal_chain.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-04-11
# Desc:
#   交易信号到执行结果调用链相关单测（与计划「信号到成交调用链」对齐）。
# ======================================
#
# --- 摘录：图 A 回测链（calculate_trade_results 内部）---
# flowchart TD
#   BS[backtest_step] --> CTR[calculate_trade_results]
#   CTR -->|"PT"| TRIM[trim_pt_type_signals] --> PT[parse_pt_signals]
#   CTR -->|"PS"| PS[parse_ps_signals]
#   CTR -->|"VS"| VS[parse_vs_signals]
#   PT --> ADJ[数组级调整]
#   PS --> ADJ
#   VS --> ADJ
#   ADJ --> GSR[get_selling_result] --> GPR[get_purchase_result] --> AES[apply_execution_slippage]
#
# --- 摘录：图 B 实盘链（parse_live_trade_signal）---
# flowchart TD
#   PTS[parse_live_trade_signal] -->|"PT"| TRIM --> PT
#   PTS -->|"PS"| PS
#   PTS -->|"VS"| VS
#   PT --> SCALE[own_cash 缩放]
#   PS --> SCALE
#   VS --> SCALE
#   SCALE --> STE[_signal_to_order_elements] -->|"多头买入"| GPR[get_purchase_result]
#
# --- 摘录：图 C 同构/分叉要点 ---
# - 共享：trim / parse_pt|ps|vs、买入侧 get_purchase_result。
# - 仅回测：get_selling_result、apply_execution_slippage、CTR 内完整计划→成交。
# - 仅实盘结构：parse_live_trade_signal、_signal_to_order_elements；卖出不经 get_selling_result。
# - parse_live_trade_signal 先按 own_cash 缩放计划买入，_signal_to_order_elements 再按 available_cash 缩放。
#
import inspect
import unittest

import numpy as np

from qteasy.finance import get_purchase_result
from qteasy.trader import Trader
from qteasy.trading_util import parse_live_trade_signal, trim_pt_type_signals


class TestTraderParseLiveTradeSignalContract(unittest.TestCase):
    """通过源码反射核对 Trader._run_strategy 对 parse_live_trade_signal 的实参契约。"""

    def test_trader_run_strategy_passes_parse_live_trade_signal_kwargs(self):
        print('\n[TestTraderParseLiveTradeSignalContract] inspect Trader._run_strategy -> parse_live_trade_signal')
        src = inspect.getsource(Trader._run_strategy)
        print('source contains parse_live_trade_signal call block (snippet):')
        for needle in (
                'parse_live_trade_signal(',
                'signals=op_signal',
                'signal_type=signal_type',
                'shares=shares',
                'prices=current_prices',
                'own_amounts=own_amounts',
                'own_cash=own_cash',
                'available_amounts=available_amounts',
                'available_cash=available_cash',
                'cost_params=self.cost_params',
                'pt_buy_threshold=self.pt_buy_threshold',
                'pt_sell_threshold=self.pt_sell_threshold',
                'allow_sell_short=self.allow_sell_short',
                'trade_batch_size=self.trade_batch_size',
                'sell_batch_size=self.sell_batch_size',
                'long_position_limit=self.long_position_limit',
                'short_position_limit=self.short_position_limit',
        ):
            self.assertIn(needle, src, msg=f'missing kwarg or call marker: {needle}')
            print('  ok:', needle)


class TestTrimPtTypeSignalsPlanned(unittest.TestCase):
    """§1 trim_pt_type_signals 拟定表 TRIM-P1～P3。"""

    def test_trim_pt_type_signals_trim_p1_long_sum_exceeds_limit(self):
        print('\n[TestTrimPtTypeSignalsPlanned] TRIM-P1 long sum 1.1 -> scale to 1.0')
        op = np.array([0.6, 0.5], dtype=np.float64)
        out = trim_pt_type_signals(op, 1.0, -1.0)
        exp = np.array([6.0 / 11.0, 5.0 / 11.0], dtype=np.float64)
        print('  op:', op, 'out:', out, 'expected:', exp)
        self.assertTrue(np.allclose(out, exp), msg=f'got {out}')

    def test_trim_pt_type_signals_trim_p2_short_sum_below_limit(self):
        print('\n[TestTrimPtTypeSignalsPlanned] TRIM-P2 short sum -0.9 -> scale to -0.8')
        op = np.array([-0.4, -0.5], dtype=np.float64)
        out = trim_pt_type_signals(op, 1.0, -0.8)
        exp = np.array([-0.8 * 4.0 / 9.0, -0.8 * 5.0 / 9.0], dtype=np.float64)
        print('  op:', op, 'out:', out, 'expected:', exp)
        self.assertTrue(np.allclose(out, exp), msg=f'got {out}')

    def test_trim_pt_type_signals_trim_p3_no_scaling(self):
        print('\n[TestTrimPtTypeSignalsPlanned] TRIM-P3 within limits, unchanged')
        op = np.array([0.3, -0.2], dtype=np.float64)
        out = trim_pt_type_signals(op, 1.0, -1.0)
        print('  op:', op, 'out:', out)
        self.assertTrue(np.allclose(out, op), msg=f'got {out}')


class TestParseLiveTradeSignalPlanned(unittest.TestCase):
    """§6.4 / §6.5 parse_live_trade_signal 拟定项。"""

    def test_pts_oc_own_cash_scales_then_matches_get_purchase_result(self):
        print('\n[TestParseLiveTradeSignalPlanned] PTS-OC own_cash=5000, PS plan sum 20000 -> scale 0.25')
        shares = ['A']
        prices = np.array([10.0])
        own_amounts = np.array([0.0])
        own_cash = 5000.0
        signals = np.array([4.0])
        cost_params = np.array([0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
        parsed = parse_live_trade_signal(
                signals=signals,
                signal_type='ps',
                shares=shares,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                available_amounts=own_amounts,
                available_cash=own_cash,
                cost_params=cost_params,
                allow_sell_short=True,
                trade_batch_size=0.0,
                sell_batch_size=0.0,
        )
        symbols, positions, directions, quantities, quoted_prices, remarks = parsed
        print('  parsed symbols', symbols, 'qty', quantities, 'qp', quoted_prices, 'remarks', remarks)
        self.assertEqual(symbols, ['A'])
        self.assertEqual(directions, ['buy'])
        self.assertAlmostEqual(quantities[0], 500.0)
        ap, cs, fees = get_purchase_result(prices, np.array([5000.0]), 0.0, cost_params)
        print('  get_purchase_result qty', ap[0], 'fees', fees[0], 'cash_spent', cs[0])
        self.assertAlmostEqual(float(ap[0]), 500.0)
        self.assertAlmostEqual(float(fees[0]), 0.0)
        self.assertAlmostEqual(float(cs[0]), -5000.0)
        notional = float(quantities[0]) * float(prices[0])
        print('  notional', notional)
        self.assertLessEqual(notional, own_cash + 1e-9)

    def test_pts_err_unknown_signal_type_raises(self):
        print('\n[TestParseLiveTradeSignalPlanned] PTS-ERR unknown signal_type')
        with self.assertRaises(ValueError) as ctx:
            parse_live_trade_signal(
                    signals=np.array([1.0]),
                    signal_type='xx',
                    shares=['A'],
                    prices=np.array([10.0]),
                    own_amounts=np.array([0.0]),
                    own_cash=1.0,
            )
        print('  message:', str(ctx.exception))
        self.assertIn('Unknown signal type', str(ctx.exception))

    def test_pts_cost_short_cost_params_raises(self):
        print('\n[TestParseLiveTradeSignalPlanned] PTS-COST cost_params size < 5')
        with self.assertRaises(ValueError) as ctx:
            parse_live_trade_signal(
                    signals=np.array([100.0]),
                    signal_type='vs',
                    shares=['A'],
                    prices=np.array([10.0]),
                    own_amounts=np.array([0.0]),
                    own_cash=1e9,
                    cost_params=np.array([0.0, 0.0, 0.0]),
            )
        print('  message:', str(ctx.exception))
        self.assertIn('cost_params must have at least 5 elements', str(ctx.exception))

    def test_pts_qp_quoted_prices_and_remarks_types_pl_a1_style(self):
        print('\n[TestParseLiveTradeSignalPlanned] PTS-QP quoted_prices / remarks on PT multi-leg')
        shares = ['000001', '000002', '000003']
        prices = np.array([20.0, 20.0, 20.0])
        own_amounts = np.array([500.0, 500.0, 1000.0])
        own_cash = 100000.0
        cost_params = np.zeros(5, dtype=np.float64)
        parsed = parse_live_trade_signal(
                signals=np.array([0.1, 0.1, 0.1]),
                signal_type='pt',
                shares=shares,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                available_amounts=own_amounts,
                available_cash=own_cash,
                cost_params=cost_params,
                allow_sell_short=True,
                trade_batch_size=100,
                sell_batch_size=1,
        )
        sy, pos, dire, qty, qp, rmks = parsed
        print('  symbols', sy, 'qty', qty, 'qp', qp, 'remarks', rmks)
        self.assertEqual(len(qp), len(sy))
        self.assertEqual(len(rmks), len(sy))
        for i, s in enumerate(sy):
            idx = shares.index(s)
            self.assertAlmostEqual(qp[i], prices[idx])
            self.assertIsInstance(rmks[i], str)

    def test_pts_nz_nonzero_fee_vs_end_to_end_matches_kernel(self):
        print('\n[TestParseLiveTradeSignalPlanned] §6.5 non-zero fee VS vs get_purchase_result')
        shares = ['ETF1']
        prices = np.array([10.0])
        own_amounts = np.array([0.0])
        own_cash = 1e9
        signals = np.array([120.0])
        cost_params = np.array([0.003, 0.001, 5.0, 5.0, 0.0], dtype=np.float64)
        parsed = parse_live_trade_signal(
                signals=signals,
                signal_type='vs',
                shares=shares,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=own_cash,
                available_amounts=own_amounts,
                available_cash=own_cash,
                cost_params=cost_params,
                allow_sell_short=False,
                trade_batch_size=100.0,
                sell_batch_size=100.0,
        )
        qty = parsed[3]
        qp = parsed[4]
        print('  quantities', qty, 'quoted_prices', qp)
        self.assertEqual(len(qty), 1)
        self.assertAlmostEqual(qty[0], 100.0)
        self.assertAlmostEqual(qp[0], 10.0)
        ap, cs, fees = get_purchase_result(prices, np.array([1205.0]), 100.0, cost_params)
        print('  kernel ap', ap[0], 'fees', fees[0], 'cash_spent', cs[0])
        self.assertAlmostEqual(float(ap[0]), qty[0])
        # max(100*10*0.003, buy_min=5) = 5
        self.assertAlmostEqual(float(fees[0]), 5.0)
        self.assertAlmostEqual(float(cs[0]), -1005.0)


if __name__ == '__main__':
    unittest.main()
