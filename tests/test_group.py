# coding=utf-8
# ======================================
# File:     test_group.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-08-11
# Desc:
#   Unittest for all strategy group
# properties and methods.
# ======================================

import unittest

import numpy as np

from qteasy.group import Group
from qteasy.parameter import Parameter
from qteasy.datatypes import DataType
from qteasy.strategy import RuleIterator, GeneralStg, FactorSorter


class TestGroup(unittest.TestCase):

    def setUp(self):
        class GenStg(GeneralStg):
            """第一个测试交易策略类，继承自GeneralStg

            包含两个可调参数: `param1` 和 `param2`，用于测试参数传递和使用。
            使用三种不同的数据类型: 'price@5minx30', 'volume@hx10', 'indicator@dx5'，用于测试数据类型的处理。
            """
            param1 = Parameter(
                name='param1',
                par_type='int',
                par_range=(1, 100),
                value=50,
            )
            param2 = Parameter(
                name='param2',
                par_type='int',
                par_range=(2, 50),
                value=25,
            )
            dtype_1 = DataType(
                name='close',
                freq='d',
                asset_type='E',
            )
            dtype_3 = DataType(
                name='close',
                freq='5min',
                asset_type='E',
            )

            def __init__(self, par_values: tuple = None, *, run_timing='close', run_freq='d'):
                super().__init__(
                        name='test_gen',
                        description='test general strategy',
                        run_freq=run_freq,
                        run_timing=run_timing,
                        pars=[self.param1, self.param2],
                        data_types={'close_E_d': self.dtype_1, 'close_E_5min': self.dtype_3},
                        use_latest_data_cycle=[True, False],
                        window_length=[7, 9],
                )

                if par_values:
                    self.update_par_values(*par_values)

            def realize(self):

                print("GeneralStg realized")
                print(f"got datas:\n{self.close_E_d}\n and \n{self.close_E_5min}")
                dt1_avg = np.mean(self.close_E_d, axis=0)
                dt2_avg = np.mean(self.close_E_5min, axis=0)
                print(f"average 1: \n{dt1_avg}, \naverage 2: \n{dt2_avg}")
                avg = dt1_avg * self.param1 + dt2_avg * self.param2
                print(f'avg = avg1 * {self.param1} + avg2 * {self.param2} = \n{avg}')
                signal = np.zeros_like(avg)
                signal[np.argmax(avg)] = 1
                print(f'got signal: \n{signal}')

                return signal

        class FactorSorterStg(FactorSorter):

            param1 = Parameter(
                name='param1',
                par_type='int',
                par_range=(1, 100),
                value=50,
            )
            param2 = Parameter(
                name='param2',
                par_type='int',
                par_range=(2, 50),
                value=25,
            )
            dtype_1 = DataType(
                name='close',
                freq='d',
                asset_type='E',
            )
            dtype_3 = DataType(
                name='close',
                freq='5min',
                asset_type='E',
            )

            def __init__(self, par_values=None, *, run_timing='d', run_freq='close', **kwargs):
                super().__init__(
                        name='test_factor_sorter',
                        description='test factor sorter strategy',
                        run_freq=run_freq,
                        run_timing=run_timing,
                        pars=[self.param1, self.param2],
                        data_types={'close_E_d': self.dtype_1, 'close_E_5min': self.dtype_3},
                        use_latest_data_cycle=[True, False],
                        window_length=[7, 9],
                        **kwargs,
                )

                if par_values:
                    self.update_par_values(*par_values)

            def realize(self):
                print("FactorSorter realized")
                print(f"got datas:\n{self.close_E_d}\n and \n{self.close_E_5min}")
                dt1_avg = np.mean(self.close_E_d, axis=0)
                dt2_avg = np.mean(self.close_E_5min, axis=0)
                print(f"average 1: \n{dt1_avg}, \naverage 2: \n{dt2_avg}")
                avg = dt1_avg * self.param1 + dt2_avg * self.param2
                print(f'signal sorter = avg1 * {self.param1} + avg2 * {self.param2} = \n{avg}')

                return avg

        class RuleIteratorStg(RuleIterator):

            param1 = Parameter(
                name='param1',
                par_type='int',
                par_range=(1, 100),
                value=50,
            )
            param2 = Parameter(
                name='param2',
                par_type='int',
                par_range=(2, 50),
                value=25,
            )
            dtype_1 = DataType(
                name='close',
                freq='d',
                asset_type='E',
            )
            dtype_3 = DataType(
                name='close',
                freq='5min',
                asset_type='E',
            )

            def __init__(self, par_values=None, *, run_timing='d', run_freq='close'):
                super().__init__(
                        name='test_rule_iterator',
                        description='test rule iterator strategy',
                        run_freq=run_freq,
                        run_timing=run_timing,
                        # TODO: user-defined parameter names should also be allowed
                        pars=[self.param1, self.param2],
                        # TODO: user-defined dtype names should be allowed using {name: Dtype} form
                        data_types={'close_E_d': self.dtype_1, 'close_E_5min': self.dtype_3},
                        use_latest_data_cycle=[True, False],
                        window_length=[7, 9],
                )

                if par_values:
                    self.update_par_values(*par_values)

            def realize(self):
                print("RuleIterator realized")
                print(f"got datas:\n{self.close_E_d}\n and \n{self.close_E_5min}")
                dt1_avg = np.mean(self.close_E_d, axis=0)
                dt2_avg = np.mean(self.close_E_5min, axis=0)
                print(f"average 1: \n{dt1_avg}, \naverage 2: \n{dt2_avg}")
                criteria = dt1_avg * self.param1 >= dt2_avg * self.param2
                print(f'criteria = avg1 * {self.param1} >= avg2 * {self.param2} = {criteria}')
                if criteria:
                    return 1
                else:
                    return 0

        # 实例化测试策略类
        self.gen_stg_d_close = GenStg(run_freq='d', run_timing='close')
        self.gen_stg_h_close = GenStg(par_values=(50, 20), run_freq='h', run_timing='close')
        self.gen_stg_h_open = GenStg(par_values=(50, 15), run_freq='h', run_timing='open')

        self.factor_sorter_d_close = FactorSorterStg(par_values=(10, 14), run_freq='d', run_timing='close')
        self.factor_sorter_h_close = FactorSorterStg(par_values=(10, 15), run_freq='h', run_timing='close')
        self.factor_sorter_h_open = FactorSorterStg(run_freq='h', run_timing='open')

        self.iterator_stg_d_close = RuleIteratorStg(run_freq='d', run_timing='close')
        self.iterator_stg_h_close = RuleIteratorStg(run_freq='h', run_timing='close')
        self.iterator_stg_d_930 = RuleIteratorStg(run_freq='d', run_timing='9:30')

    def test_creation(self):
        gp = Group('new_group', signal_type='PS', blender='')

        self.assertIsInstance(gp, Group)
        self.assertEqual(gp.name, 'new_group')
        self.assertEqual(gp.run_freq, None)
        self.assertEqual(gp.run_timing, None)
        self.assertEqual(gp.signal_type, 'PS')

        # test creating groups with different parameters
        gp = Group(name='name', blender='s1 + s2')
        self.assertEqual(gp.signal_type, 'PT')
        self.assertEqual(gp.members, [])

        # test creating groups with wrong parameters
        self.assertRaises(TypeError, Group, 35)  # wrong type
        self.assertRaises(ValueError, Group, 'name', signal_type='wrong_type')
        self.assertRaises(TypeError, Group, 'name', signal_type=24)
        self.assertRaises(ValueError, Group, 'name', blender='wrong blender')

    def test_add_strategy(self):
        gp = Group('new_group')

        self.assertEqual(gp.name, 'new_group')
        self.assertEqual(gp.run_freq, None)
        self.assertEqual(gp.run_timing, None)
        self.assertEqual(gp.blender, None)
        self.assertEqual(gp.human_blender, '')

        gp.add_strategy(self.gen_stg_d_close)

        self.assertEqual(gp.run_freq, 'd')
        self.assertEqual(gp.run_timing, 'close')
        self.assertEqual(gp.blender_str, '')
        self.assertEqual(gp.human_blender, '')
        gp.blender_str = 's0 + 3'
        self.assertEqual(gp.human_blender, 'test_gen + 3')
        self.assertEqual(gp.blender, ['+', '3', 's0'])

        gp.add_strategy(self.factor_sorter_d_close)

        gp.blender_str = 's0 + s1'
        self.assertEqual(gp.human_blender, 'test_gen + test_factor_sorter')
        self.assertEqual(gp.blender, ['+', 's1', 's0'])

        self.assertRaises(ValueError, gp.add_strategy, self.factor_sorter_h_open)
        self.assertEqual(gp.run_freq, 'd')

    def test_blender(self):
        gp = Group('new_group')

        self.assertEqual(gp.name, 'new_group')
        self.assertEqual(gp.run_freq, None)
        self.assertEqual(gp.run_timing, None)
        self.assertEqual(gp.blender, None)
        self.assertEqual(gp.human_blender, '')

        gp.add_strategy(self.gen_stg_d_close)
        gp.add_strategy(self.factor_sorter_d_close)
        gp.add_strategy(self.iterator_stg_d_close)

        gp.blender_str = 's0 + s1 + s2'
        self.assertEqual(gp.human_blender, 'test_gen + test_factor_sorter + test_rule_iterator')
        self.assertEqual(gp.blender, ['+', 's2', '+', 's1', 's0'])

        signals = [
            np.array([0.7,0.5,0.3]),
            np.array([0.8,0.8,0.8]),
            np.array([0.5,0.6,0.7]),
        ]

        blended_signal = gp.blend(signals)
        print(blended_signal)
        self.assertIsInstance(blended_signal, np.ndarray)
        self.assertEqual(blended_signal.shape, (3,))
        self.assertTrue(np.allclose(blended_signal, np.array([2., 1.9, 1.8])))

        test_blender_strings = [
            's0 + s1 + s2 + s0',
            's0 * 2 + s1 * 3 - s2',
            'max(s0, s1) + s2',
            'sum(s0, s1, s2)',
            'avg(s0, s1, s2)',
            'pos_2_0.5(s0, s1, s2)',
            'avgpos_2_0.5(s0, s1, s2)',
            'power(s0, s1) + s2',
            'unify(s0) + uni(s1) + unify(s2)'
        ]

        for blender_str in test_blender_strings:
            gp.blender_str = blender_str
            print(f'Testing blender: {gp.human_blender}, \nblender: {gp.blender}\nresult\n{gp.blend(signals)}')
            self.assertIsInstance(gp.blender, list)
            self.assertTrue(all(isinstance(item, str) for item in gp.blender))


if __name__ == '__main__':
    unittest.main()