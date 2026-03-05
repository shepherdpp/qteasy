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

    @unittest.skip("TODO: enable after check_dynamic_data considers proc.* usage")
    def test_check_dynamic_data_proc_usage(self):
        """占位测试：一旦 check_dynamic_data 支持基于 proc.* 使用情况的判定，应启用本测试。"""
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
        run(op=op, mode=1, visual=False, trade_log=False)
        self.assertTrue(op.check_dynamic_data())


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


if __name__ == '__main__':
    unittest.main()

import unittest
import numpy as np

from qteasy import GeneralStg, StgData, Parameter, run, configure, Operator


class StaticOnlyStg(GeneralStg):
    """仅依赖静态历史数据的简单策略，用于测试 check_dynamic_data() 的静态分支。"""

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


class DynamicOnlyStg(GeneralStg):
    """仅声明动态数据类型的策略，用于测试 dynamic data type 检测。"""

    def __init__(self):
        super().__init__(
                name='DynamicOnly',
                description='dynamic only strategy',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=StgData('op_cashes', freq='d', asset_type='E', window_length=5),
        )

    def realize(self):
        return np.zeros(self.share_count, dtype=float)


class MixedStg(GeneralStg):
    """同时声明静态与动态数据类型的策略，用于测试 mixed 检测。"""

    def __init__(self):
        super().__init__(
                name='MixedStg',
                description='mixed static and dynamic data types',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=[
                    StgData('close', freq='d', asset_type='E', window_length=5),
                    StgData('op_cashes', freq='d', asset_type='E', window_length=5),
                    StgData('op_trade_volumes', freq='d', asset_type='E', window_length=5),
                ],
        )

    def realize(self):
        _ = self.get_data('close_E_d')
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
        return np.full(self.share_count, 0.5, dtype=float)


class DynamicTaggedButStaticLogicStg(GeneralStg):
    """声明动态数据类型，但逻辑与 StaticSignalStg 一致，不访问 proc.*。"""

    def __init__(self):
        super().__init__(
                name='DynamicTaggedStaticLogic',
                description='dynamic-tagged but static logic',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=[
                    StgData('close', freq='d', asset_type='E', window_length=5),
                    StgData('op_cashes', freq='d', asset_type='E', window_length=5),
                ],
        )

    def realize(self):
        return np.full(self.share_count, 0.5, dtype=float)


class ProcAPITestStg(GeneralStg):
    """用于测试 get_data('proc.*') API 行为的策略。"""

    def __init__(self):
        super().__init__(
                name='ProcAPITest',
                description='test proc.* get_data API',
                pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                data_types=[
                    StgData('close', freq='d', asset_type='E', window_length=5),
                    StgData('op_cashes', freq='d', asset_type='E', window_length=5),
                    StgData('op_trade_volumes', freq='d', asset_type='E', window_length=5),
                ],
        )

    def realize(self):
        _ = self.get_data('close_E_d')
        own_cash_hist = self.get_data('proc.own_cash')
        assert isinstance(own_cash_hist, np.ndarray)
        return np.zeros(self.share_count, dtype=float)


class TestDynamicDataTypeDetection(unittest.TestCase):
    """测试 Operator.check_dynamic_data() 与 all_dynamic_dtypes 检测逻辑。"""

    def test_check_dynamic_data_static_only(self):
        op = Operator(strategies=[StaticOnlyStg()])
        self.assertFalse(op.check_dynamic_data())
        self.assertEqual(len(op.all_dynamic_dtypes), 0)

    def test_check_dynamic_data_dynamic_only(self):
        op = Operator(strategies=[DynamicOnlyStg()])
        self.assertTrue(op.check_dynamic_data())
        self.assertSetEqual(set(op.all_dynamic_dtypes.keys()), {'op_cashes'})

    def test_check_dynamic_data_mixed_single_strategy(self):
        op = Operator(strategies=[MixedStg()])
        self.assertTrue(op.check_dynamic_data())
        self.assertSetEqual(set(op.all_dynamic_dtypes.keys()),
                            {'op_cashes', 'op_trade_volumes'})

    def test_check_dynamic_data_mixed_multiple_strategies(self):
        op = Operator(strategies=[StaticOnlyStg(), DynamicOnlyStg(), MixedStg()])
        self.assertTrue(op.check_dynamic_data())
        self.assertSetEqual(set(op.all_dynamic_dtypes.keys()),
                            {'op_cashes', 'op_trade_volumes'})


class TestDynamicVsStaticBacktestEquivalence(unittest.TestCase):
    """不使用 proc.* 的情况下，静态/动态分支回测结果应一致。"""

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

    def test_static_and_dynamic_backtest_equivalence_without_proc_usage(self):
        bt_static = self._run_with_strategy(StaticSignalStg)
        bt_dynamic = self._run_with_strategy(DynamicTaggedButStaticLogicStg)

        np.testing.assert_allclose(bt_static.own_cashes, bt_dynamic.own_cashes)
        np.testing.assert_allclose(bt_static.available_cashes, bt_dynamic.available_cashes)
        np.testing.assert_allclose(bt_static.own_amounts_array, bt_dynamic.own_amounts_array)
        np.testing.assert_allclose(bt_static.available_amounts_array, bt_dynamic.available_amounts_array)
        np.testing.assert_allclose(bt_static.trade_records_array, bt_dynamic.trade_records_array)
        np.testing.assert_allclose(bt_static.trade_cost_array, bt_dynamic.trade_cost_array)


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

        op, res = self._run_with_strategy(StaticAPITestStg)
        self.assertIsInstance(res, dict)
        self.assertIn('complete_values', res)

    def test_get_data_static_rejects_lag_window(self):
        class StaticLagWindowStg(GeneralStg, unittest.TestCase):
            def __init__(self):
                GeneralStg.__init__(
                        self,
                        name='StaticLagWin',
                        description='static lag/window test',
                        pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                        data_types=StgData('close', freq='d', asset_type='E', window_length=5),
                )

            def realize(self):
                with self.assertRaises(ValueError):
                    _ = self.get_data('close_E_d', lag=1)
                with self.assertRaises(ValueError):
                    _ = self.get_data('close_E_d', window='5d')
                return np.zeros(self.share_count, dtype=float)

        op, res = self._run_with_strategy(StaticLagWindowStg)
        self.assertIsInstance(res, dict)

    def test_get_data_proc_single_field_ok(self):
        op, res = self._run_with_strategy(ProcAPITestStg)
        self.assertIsInstance(res, dict)
        self.assertIn('complete_values', res)

    def test_get_data_proc_multiple_fields_not_allowed(self):
        class MultiProcFieldStg(GeneralStg, unittest.TestCase):
            def __init__(self):
                GeneralStg.__init__(
                        self,
                        name='MultiProcField',
                        description='multi proc field test',
                        pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                        data_types=[
                            StgData('close', freq='d', asset_type='E', window_length=5),
                            StgData('op_cashes', freq='d', asset_type='E', window_length=5),
                            StgData('op_trade_volumes', freq='d', asset_type='E', window_length=5),
                        ],
                )

            def realize(self):
                with self.assertRaises(ValueError):
                    _ = self.get_data('proc.own_cash', 'proc.own_amounts')
                return np.zeros(self.share_count, dtype=float)

        op, res = self._run_with_strategy(MultiProcFieldStg)
        self.assertIsInstance(res, dict)

    def test_get_data_cannot_mix_static_and_proc(self):
        class MixStaticProcStg(GeneralStg, unittest.TestCase):
            def __init__(self):
                GeneralStg.__init__(
                        self,
                        name='MixStaticProc',
                        description='mix static and proc test',
                        pars=[Parameter((0, 1), name='dummy', par_type='int', value=0)],
                        data_types=[
                            StgData('close', freq='d', asset_type='E', window_length=5),
                            StgData('op_cashes', freq='d', asset_type='E', window_length=5),
                        ],
                )

            def realize(self):
                with self.assertRaises(ValueError):
                    _ = self.get_data('close_E_d', 'proc.own_cash')
                return np.zeros(self.share_count, dtype=float)

        op, res = self._run_with_strategy(MixStaticProcStg)
        self.assertIsInstance(res, dict)


if __name__ == '__main__':
    unittest.main()

