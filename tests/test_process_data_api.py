# coding=utf-8
# ======================================
# File:     test_process_data_api.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-03-05
# Desc:
#   Unittests for process data (proc.*)
#   and dynamic backtest behavior in
#   qteasy.
# ======================================
import unittest
import numpy as np

from qteasy import GeneralStg, StgData, Parameter, run, configure, Operator


class StaticOnlyStg(GeneralStg):
    """仅依赖静态历史数据的简单策略，用于测试静态场景。"""

    def __init__(self):
        super().__init__(
                name='StaticOnly',
                description='static only strategy',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=StgData('close', freq='d', asset_type='E', window_length=5),
        )

    def realize(self):
        _ = self.get_data('close_E_d')
        return np.zeros(self.share_count, dtype=float)


class ProcUserStg(GeneralStg):
    """在策略中实际调用 proc.* 接口的策略，用于测试 process data API。"""

    def __init__(self):
        super().__init__(
                name='ProcUser',
                description='strategy using process data',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=StgData('close', freq='d', asset_type='E', window_length=5),
        )

    def realize(self):
        _ = self.get_data('close_E_d')
        # 实际访问一次 proc.own_cash，检验接口可用
        own_cash_hist = self.get_data('proc.own_cash')
        assert isinstance(own_cash_hist, np.ndarray)
        return np.zeros(self.share_count, dtype=float)


class StaticSignalStg(GeneralStg):
    """纯静态策略：只依赖静态数据生成简单确定性的 PT 信号。"""

    def __init__(self):
        super().__init__(
                name='StaticSignal',
                description='static-only signal',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=StgData('close', freq='d', asset_type='E', window_length=5),
        )

    def realize(self):
        # 简单的等权 PT 信号
        return np.full(self.share_count, 0.5, dtype=float)


class ProcAwareButStaticLogicStg(GeneralStg):
    """调用 proc.* 但不将结果用于交易逻辑的策略，用于等价性测试。"""

    def __init__(self):
        super().__init__(
                name='ProcAwareStatic',
                description='proc-aware but static logic',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=StgData('close', freq='d', asset_type='E', window_length=5),
        )

    def realize(self):
        _ = self.get_data('close_E_d')
        # 访问一次 proc.own_cash，但不参与信号计算
        _ = self.get_data('proc.own_cash')
        return np.full(self.share_count, 0.5, dtype=float)


class TestDynamicDataTypeDetection(unittest.TestCase):
    """测试 Operator 在当前实现下对动态依赖的判定（以 static-only 场景为主）。"""

    def test_check_dynamic_data_static_only(self):
        print('\n[TestDynamicDataTypeDetection] static_only: check_dynamic_data should be False')
        op = Operator(strategies=[StaticOnlyStg()])
        # 纯静态策略不应被视为依赖动态过程数据
        self.assertFalse(op.check_dynamic_data())

    def test_check_dynamic_data_proc_usage(self):
        """使用 proc.* 的策略应使 check_dynamic_data() 返回 True，从而走动态回测分支。"""
        print('\n[TestDynamicDataTypeDetection] proc_usage: check_dynamic_data should be True')
        shares = ['000001.SZ', '000002.SZ']
        configure(
                asset_pool=shares,
                asset_type='E',
                invest_start='20200102',
                invest_end='20200110',
                invest_cash_amounts=[100000.0],
                trade_batch_size=100,
                sell_batch_size=100,
        )
        op = Operator(strategies=[ProcUserStg()],
                      signal_type='PT',
                      run_freq='d',
                      run_timing='close')
        self.assertTrue(op.check_dynamic_data(), 'Operator with proc.* usage should require dynamic backtest')
        run(op=op, mode=1, visual=False, trade_log=False)
        self.assertIsNotNone(op.backtested)
        print('  check_dynamic_data():', op.check_dynamic_data(), ', backtest completed.')


class TestDynamicVsStaticBacktestEquivalence(unittest.TestCase):
    """不使用 proc.* 结果参与计算时，静态/动态感知策略的回测结果应一致。"""

    def _run_with_strategy(self, strategy_cls):
        shares = ['000001.SZ', '000002.SZ']
        configure(
                asset_pool=shares,
                asset_type='E',
                invest_start='20200102',
                invest_end='20200120',
                invest_cash_amounts=[100000.0],
                trade_batch_size=100,
                sell_batch_size=100,
        )
        op = Operator(strategies=[strategy_cls()],
                      signal_type='PT',
                      run_freq='d',
                      run_timing='close')
        _ = run(op=op, mode=1, visual=False, trade_log=False)
        return op.backtested

    def test_static_and_proc_aware_backtest_equivalence_without_using_proc_results(self):
        """StaticSignal 与 ProcAwareButStaticLogic 使用相同静态逻辑，应产生完全一致的回测数组。"""
        print('\n[TestDynamicVsStaticBacktestEquivalence] comparing StaticSignal vs ProcAwareStatic backtest arrays')
        bt_static = self._run_with_strategy(StaticSignalStg)
        bt_proc_aware = self._run_with_strategy(ProcAwareButStaticLogicStg)

        print('  own_cashes shapes:', bt_static.own_cashes.shape, bt_proc_aware.own_cashes.shape)
        print('  own_amounts_array shapes:', bt_static.own_amounts_array.shape, bt_proc_aware.own_amounts_array.shape)

        np.testing.assert_allclose(bt_static.own_cashes, bt_proc_aware.own_cashes)
        np.testing.assert_allclose(bt_static.available_cashes, bt_proc_aware.available_cashes)
        np.testing.assert_allclose(bt_static.own_amounts_array, bt_proc_aware.own_amounts_array)
        np.testing.assert_allclose(bt_static.available_amounts_array, bt_proc_aware.available_amounts_array)
        np.testing.assert_allclose(bt_static.trade_records_array, bt_proc_aware.trade_records_array)
        np.testing.assert_allclose(bt_static.trade_cost_array, bt_proc_aware.trade_cost_array)


class TestProcessDataAPI(unittest.TestCase):
    """测试 get_data('proc.*') 接口在回测中的行为。"""

    def _run_with_strategy(self, strategy_cls):
        shares = ['000001.SZ', '000002.SZ']
        configure(
                asset_pool=shares,
                asset_type='E',
                invest_start='20200102',
                invest_end='20200110',
                invest_cash_amounts=[100000.0],
                trade_batch_size=100,
                sell_batch_size=100,
        )
        op = Operator(strategies=[strategy_cls()],
                      signal_type='PT',
                      run_freq='d',
                      run_timing='close')
        res = run(op=op, mode=1, visual=False, trade_log=False)
        return op, res

    def test_get_data_static_multi_sources_no_lag_window(self):
        class StaticAPITestStg(GeneralStg):
            def __init__(self):
                super().__init__(
                        name='StaticAPI',
                        description='static api test',
                        pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                        data_types=[
                            StgData('close', freq='d', asset_type='E', window_length=5),
                            StgData('high', freq='d', asset_type='E', window_length=5),
                        ],
                )

            def realize(self):
                close = self.get_data('close_E_d')
                close2, high = self.get_data('close_E_d', 'high_E_d')
                assert isinstance(close, np.ndarray)
                assert isinstance(close2, np.ndarray)
                assert isinstance(high, np.ndarray)
                return np.zeros(self.share_count, dtype=float)

        print('\n[TestProcessDataAPI] static multi-sources without lag/window')
        _, res = self._run_with_strategy(StaticAPITestStg)
        self.assertIsInstance(res, dict)
        self.assertIn('complete_values', res)

    def test_get_data_static_rejects_lag_window(self):
        class StaticLagWindowStg(GeneralStg):
            def __init__(self):
                super().__init__(
                        name='StaticLagWin',
                        description='static lag/window test',
                        pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                        data_types=StgData('close', freq='d', asset_type='E', window_length=5),
                )

            def realize(self):
                # 静态数据不应接受 lag/window 参数
                try:
                    _ = self.get_data('close_E_d', lag=1)
                except ValueError:
                    pass
                else:
                    raise AssertionError('static get_data should raise ValueError when lag is given')

                try:
                    _ = self.get_data('close_E_d', window='5d')
                except ValueError:
                    pass
                else:
                    raise AssertionError('static get_data should raise ValueError when window is given')
                return np.zeros(self.share_count, dtype=float)

        print('\n[TestProcessDataAPI] static data should reject lag/window')
        _, res = self._run_with_strategy(StaticLagWindowStg)
        self.assertIsInstance(res, dict)

    def test_get_data_proc_single_field_ok(self):
        print('\n[TestProcessDataAPI] single proc.* field should be accepted')
        op, res = self._run_with_strategy(ProcUserStg)
        print('  backtested signals:', op.backtested.n_signals if hasattr(op, "backtested") else "N/A")
        self.assertIsInstance(res, dict)
        self.assertIn('complete_values', res)

    def test_get_data_proc_multiple_fields_not_allowed(self):
        class MultiProcFieldStg(GeneralStg):
            def __init__(self):
                super().__init__(
                        name='MultiProcField',
                        description='multi proc field test',
                        pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                        data_types=StgData('close', freq='d', asset_type='E', window_length=5),
                )

            def realize(self):
                try:
                    _ = self.get_data('proc.own_cash', 'proc.own_amounts')
                except ValueError:
                    pass
                else:
                    raise AssertionError('get_data() should reject multiple proc.* fields in one call')
                return np.zeros(self.share_count, dtype=float)

        print('\n[TestProcessDataAPI] multiple proc.* fields in one get_data() should be rejected')
        _, res = self._run_with_strategy(MultiProcFieldStg)
        self.assertIsInstance(res, dict)

    def test_get_data_cannot_mix_static_and_proc(self):
        class MixStaticProcStg(GeneralStg):
            def __init__(self):
                super().__init__(
                        name='MixStaticProc',
                        description='mix static and proc test',
                        pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                        data_types=StgData('close', freq='d', asset_type='E', window_length=5),
                )

            def realize(self):
                try:
                    _ = self.get_data('close_E_d', 'proc.own_cash')
                except ValueError:
                    pass
                else:
                    raise AssertionError('get_data() should reject mixing static and proc.* in one call')
                return np.zeros(self.share_count, dtype=float)

        print('\n[TestProcessDataAPI] mixing static and proc.* in one get_data() should be rejected')
        _, res = self._run_with_strategy(MixStaticProcStg)
        self.assertIsInstance(res, dict)


class NoLookAheadStg(GeneralStg):
    """用于测试 proc.trade_records 在动态回测中不包含当前步尚未成交结果。"""

    def __init__(self):
        super().__init__(
                name='NoLookAhead',
                description='no look-ahead test strategy',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=StgData('close', freq='d', asset_type='E', window_length=1),
        )
        # 记录每一步在 realize() 中看到的 trade_records 历史长度与 lag=0 的结果
        self.hist_lengths: list[int] = []
        self.last_records: list[np.ndarray] = []

    def realize(self):
        # 获取完整历史和最近一次 trade_records 视图
        hist = self.get_data('proc.trade_records')
        self.hist_lengths.append(0 if hist.size == 0 else hist.shape[0])
        if hist.size == 0:
            # 第一步没有历史成交记录
            self.last_records.append(None)
        else:
            last = self.get_data('proc.trade_records', lag=0)
            # last 形状通常为 (1, share_count)
            self.last_records.append(last.copy())
        # 输出零信号，避免对路径产生额外影响
        return np.zeros(self.share_count, dtype=float)


class TestNoLookAheadForProcessData(unittest.TestCase):
    """D 组：验证 proc.trade_records 等过程数据不发生前视。"""

    def test_proc_trade_records_no_look_ahead(self):
        print('\n[TestNoLookAheadForProcessData] verifying proc.trade_records has no look-ahead')
        shares = ['000001.SZ', '000002.SZ']
        configure(
                asset_pool=shares,
                asset_type='E',
                invest_start='20200102',
                invest_end='20200110',
                invest_cash_amounts=[100000.0],
                trade_batch_size=100,
                sell_batch_size=100,
        )
        op = Operator(strategies=[NoLookAheadStg()],
                      signal_type='VS',  # 使用 VS 信号，策略返回 0，不改变路径
                      run_freq='d',
                      run_timing='close')
        res = run(op=op, mode=1, visual=False, trade_log=False)
        self.assertIsInstance(res, dict)
        backtested = op.backtested
        stg = op.strategies[0]

        print('  recorded hist_lengths:', stg.hist_lengths)
        print('  trade_records_array shape:', backtested.trade_records_array.shape)

        # 对于第 k 步（k>=1），last_records[k] 应等于 trade_records_array[k-1]
        for k, last in enumerate(stg.last_records):
            if k == 0 or last is None:
                continue
            expected = backtested.trade_records_array[k - 1]
            np.testing.assert_allclose(last.reshape(expected.shape),
                                       expected,
                                       err_msg=f'look-ahead detected at step {k}')


class VolumeBasedDynamicStg(GeneralStg):
    """E 组示例动态策略：基于最近成交量控制简单买入/持有逻辑（作为路径正确性测试样例）。"""

    def __init__(self):
        super().__init__(
                name='VolumeBasedDynamic',
                description='volume-based dynamic strategy using proc.trade_records',
                pars=[Parameter((0, 10), name='threshold', par_type='int', value=1)],
                data_types=StgData('close', freq='d', asset_type='E', window_length=1),
        )

    def realize(self):
        """示意性逻辑：如果最近一次成交绝对量大于阈值，则本步信号为 0，否则买入 1 单位。"""
        threshold = self.get_pars('threshold')
        trades_hist = self.get_data('proc.trade_records')
        if trades_hist.size == 0:
            # 第一步：发出买入信号
            return np.array([1.0] + [0.0] * (self.share_count - 1), dtype=float)
        last_trades = self.get_data('proc.trade_records', lag=0)[0]
        if np.abs(last_trades).sum() > threshold:
            # 最近一笔成交较大，本步不再加仓
            return np.zeros(self.share_count, dtype=float)
        else:
            return np.array([1.0] + [0.0] * (self.share_count - 1), dtype=float)


class TestDynamicStrategyWithProcessData(unittest.TestCase):
    """E 组：使用 process data 的真实动态策略路径正确性测试。"""

    def test_dynamic_strategy_with_process_data_correctness(self):
        """VolumeBasedDynamicStg：第一步无历史则买 1 单位第一只股票，之后每步若上步成交绝对值和不大于阈值则继续买 1 单位。"""
        print('\n[TestDynamicStrategyWithProcessData] volume-based dynamic strategy correctness')
        shares = ['000001.SZ', '000002.SZ']
        configure(
                asset_pool=shares,
                asset_type='E',
                invest_start='20200102',
                invest_end='20200110',
                invest_cash_amounts=[100000.0],
                trade_batch_size=1,
                sell_batch_size=1,
        )
        op = Operator(strategies=[VolumeBasedDynamicStg()],
                      signal_type='VS',
                      run_freq='d',
                      run_timing='close')
        res = run(op=op, mode=1, visual=False, trade_log=False)
        self.assertIsInstance(res, dict)
        backtested = op.backtested
        n_steps = backtested.own_amounts_array.shape[0] - 1  # 步数
        last_own = backtested.own_amounts_array[-1]
        print('  n_steps:', n_steps, ', last own_amounts:', last_own)

        # 策略逻辑：第一步无历史则买 1 单位第一只；之后若上步成交绝对值和不大于阈值(1)则继续买
        self.assertGreaterEqual(n_steps, 1, 'dynamic backtest should have at least one step')
        self.assertGreater(last_own[0], 0, 'first asset should have positive position (strategy buys at least once)')
        self.assertEqual(last_own[1], 0, 'second asset should remain 0 (strategy only buys first)')
        # 每步最多买 1 单位，最终持仓应在 1..n_steps 之间（具体取决于交割与阈值判断）
        self.assertLessEqual(last_own[0], n_steps + 1, 'position should not exceed one buy per step')


if __name__ == '__main__':
    unittest.main()

