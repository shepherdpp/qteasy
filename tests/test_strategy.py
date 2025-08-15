# coding=utf-8
# ======================================
# File:     test_strategy.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-07-29
# Desc:
#   Unittest for all Strategy class
# properties and methods.
# ======================================

import unittest
import numpy as np

from qteasy.strategy import (
    BaseStrategy,
    GeneralStg,
    RuleIterator,
    FactorSorter,
)

from qteasy.datatypes import DataType
from qteasy.parameter import Parameter


class TestStrategy(unittest.TestCase):
    def setUp(self):

        self.param1 = Parameter(
                name='param1',
                par_type='int',
                par_range=(1, 100),
                value=50,
        )

        self.param2 = Parameter(
                name='param2',
                par_type='float',
                par_range=(0.0, 1.0),
                value=0.5,
        )

        self.param3 = Parameter(
                name='param3',
                par_type='enum',
                par_range=('option1', 'option2', 'option3'),
                value='option1',
        )

        self.param4 = Parameter(
                name='param4',
                par_type='array[3,]',
                par_range=(1.0, 5.0),
                value=np.array([1.0, 2.0, 3.0]),
        )

        self.dtype_1 = DataType(
                name='close',
                freq='d',
                asset_type='E',
        )

        self.dtype_2 = DataType(
                name='close',
                freq='h',
                asset_type='E',
        )

        self.dtype_3 = DataType(
                name='close',
                freq='5min',
                asset_type='E',
        )

        self.dtype_4 = DataType(
                name='close',
                freq='15min',
                asset_type='E',
        )

        self.dtype_5 = DataType(
                name='close',
                freq='w',
                asset_type='E',
        )

        self.base_stg = BaseStrategy(
                name='TestStrategy',
                run_freq='d',
                run_timing='close',
                pars=[self.param1, self.param2, self.param3, self.param4],
                data_types=[self.dtype_1, self.dtype_2, self.dtype_3, self.dtype_4
                            , self.dtype_5],
                window_length=[10, 20, 30, 40, 50],
                use_latest_data_cycle=False,
        )

        # 创建三个测试交易策略类，用于测试
        class GenStg(GeneralStg):
            """第一个测试交易策略类，继承自GeneralStg

            包含两个可调参数: `param1` 和 `param2`，用于测试参数传递和使用。
            使用三种不同的数据类型: 'price@5minx30', 'volume@hx10', 'indicator@dx5'，用于测试数据类型的处理。
            """
            param1 = self.param1
            param2 = self.param2
            dtype_1 = self.dtype_1
            dtype_3 = self.dtype_3

            def __init__(self, par_values=None):
                super().__init__(
                        name='test_gen',
                        description='test general strategy',
                        run_freq='d',
                        run_timing='close',
                        pars=[self.param1, self.param2],
                        stg_type='general',
                        data_types={'dt1': self.dtype_1, 'dt2': self.dtype_3},
                        window_length=[20, 15],
                )

            def realize(self):
                print("GeneralStg realized")

        class FactorSorterStg(FactorSorter):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

            def realize(self):
                print("FactorSorter realized")

        class RuleIteratorStg(RuleIterator):
            def __init__(self):
                super().__init__()

            def realize(self):
                print("RuleIterator realized")

        # self.gen_stg = GenStg(
        #         par_values=(50, 0.5),
        # )

    def test_creation(self):
        """ test creation of strategy objects"""
        stg = self.base_stg

        self.assertIsInstance(stg, BaseStrategy)
        self.assertEqual(stg.name, 'TestStrategy')
        self.assertEqual(stg.run_freq, 'd')
        self.assertEqual(stg.run_timing, 'close')
        stg.info()
        stg.info(verbose=True)

    def test_properties(self):

        stg = self.base_stg
        # test getting basic properties like name, type, description
        self.assertEqual(stg.name, 'TestStrategy')
        self.assertEqual(stg.stg_type, 'BASE')
        self.assertEqual(stg.description, '')

        # test getting all parameters
        self.assertEqual(len(stg.pars), 4)
        self.assertEqual(stg.par_count, 4)
        self.assertEqual(stg.par_names, ['param1', 'param2', 'param3', 'param4'])
        self.assertEqual(stg.par_range,
                         {'param1':(1, 100),
                          'param2': (0.0, 1.0),
                          'param3': ('option1', 'option2', 'option3'),
                          'param4': (1.0, 5.0)})
        self.assertEqual(stg.par_types,
                         {'param1': 'int',
                          'param2': 'float',
                          'param3': 'enum',
                          'param4': 'float_array'})
        par_values = (50, 0.5, 'option1', np.array([1., 2., 3.]))
        for a, e in zip(stg.par_values, par_values):
            print(a, e)
            if isinstance(e, np.ndarray):
                self.assertTrue(np.array_equal(a, e))
            else:
                self.assertEqual(a, e)
        for items in stg.pars:
            self.assertIsInstance(stg.pars[items], Parameter)
            self.assertEqual(stg.pars[items].name, items)

        self.assertEqual(stg.param1, 50)
        self.assertEqual(stg.param2, 0.5)
        self.assertEqual(stg.param3, 'option1')
        self.assertTrue(np.array_equal(stg.param4, np.array([1.0, 2.0, 3.0])))

        # test getting all data types
        self.assertEqual(len(stg.data_types), 5)
        self.assertEqual(stg.data_type_count, 5)
        self.assertEqual(stg.data_type_ids, [
            'close_E_d',
            'close_E_h',
            'close_E_5min',
            'close_E_15min',
            'close_E_w',
        ])
        self.assertEqual(stg.data_ids, [
            'close_E_d',
            'close_E_h',
            'close_E_5min',
            'close_E_15min',
            'close_E_w',
        ])
        self.assertEqual(stg.data_names, {
            'close_E_15min': 'close',
            'close_E_5min':  'close',
            'close_E_d':     'close',
            'close_E_h':     'close',
            'close_E_w':     'close',
        })
        print(f'stg.data_freqs: {stg.data_freqs}')
        self.assertEqual(stg.data_freqs, {
            'close_E_d': 'd',
            'close_E_h': 'h',
            'close_E_5min': '5min',
            'close_E_15min': '15min',
            'close_E_w': 'w'
        })
        self.assertEqual(stg.data_ulc, {
            'close_E_d': False,
            'close_E_h': False,
            'close_E_5min': False,
            'close_E_15min': False,
            'close_E_w': False
        })
        self.assertEqual(stg.data_window_lengths, {
            'close_E_d': 10,
            'close_E_h': 20,
            'close_E_5min': 30,
            'close_E_15min': 40,
            'close_E_w': 50
        })

        self.assertEqual(stg.close_E_d, None)
        self.assertEqual(stg.close_E_h, None)
        self.assertEqual(stg.close_E_5min, None)
        self.assertEqual(stg.close_E_15min, None)
        self.assertEqual(stg.close_E_w, None)

    def test_parameters(self):
        """ test updating parameters of strategies"""
        stg = self.base_stg

        # test updating all parameters
        stg.update_par_values(75, 0.75, 'option2', np.array([2.0, 3.0, 4.0]))
        self.assertEqual(stg.param1, 75)
        self.assertEqual(stg.param2, 0.75)
        self.assertEqual(stg.param3, 'option2')
        self.assertTrue(np.array_equal(stg.param4, np.array([2.0, 3.0, 4.0])))

        par_values = (75, 0.75, 'option2', np.array([2.0, 3.0, 4.0]))
        for a, e in zip(stg.par_values, par_values):
            print(a, e)
            if isinstance(e, np.ndarray):
                self.assertTrue(np.array_equal(a, e))
            else:
                self.assertEqual(a, e)
        self.assertEqual(stg.pars['param1'].value, 75)
        self.assertEqual(stg.pars['param2'].value, 0.75)
        self.assertEqual(stg.pars['param3'].value, 'option2')
        self.assertTrue(np.array_equal(stg.pars['param4'].value, np.array([2.0, 3.0, 4.0])))

        # test updating partial parameters
        stg.update_par_values(80, 0.875)
        self.assertEqual(stg.param1, 80)
        self.assertEqual(stg.param2, 0.875)
        self.assertEqual(stg.param3, 'option2')
        self.assertTrue(np.array_equal(stg.param4, np.array([2.0, 3.0, 4.0])))

        par_values = (80, 0.875, 'option2', np.array([2.0, 3.0, 4.0]))
        for a, e in zip(stg.par_values, par_values):
            print(a, e)
            if isinstance(e, np.ndarray):
                self.assertTrue(np.array_equal(a, e))
            else:
                self.assertEqual(a, e)
        self.assertEqual(stg.pars['param1'].value, 80)
        self.assertEqual(stg.pars['param2'].value, 0.875)
        self.assertEqual(stg.pars['param3'].value, 'option2')
        self.assertTrue(np.array_equal(stg.pars['param4'].value, np.array([2.0, 3.0, 4.0])))

        # test other forms of updating parameters
        stg.update_par_values(param1=85, param2=0.5, param3='option3', param4=np.array([3.0, 4.0, 5.0]))
        self.assertEqual(stg.param1, 85)
        self.assertEqual(stg.param2, 0.5)
        self.assertEqual(stg.param3, 'option3')
        self.assertTrue(np.array_equal(stg.param4, np.array([3.0, 4.0, 5.0])))

        par_values = (85, 0.5, 'option3', np.array([3.0, 4.0, 5.0]))
        for a, e in zip(stg.par_values, par_values):
            print(a, e)
            if isinstance(e, np.ndarray):
                self.assertTrue(np.array_equal(a, e))
            else:
                self.assertEqual(a, e)
        self.assertEqual(stg.pars['param1'].value, 85)
        self.assertEqual(stg.pars['param2'].value, 0.5)
        self.assertEqual(stg.pars['param3'].value, 'option3')
        self.assertTrue(np.array_equal(stg.pars['param4'].value, np.array([3.0, 4.0, 5.0])))

        # test partial updating parameters
        stg.update_par_values(param1=95, param2=0.25)
        self.assertEqual(stg.param1, 95)
        self.assertEqual(stg.param2, 0.25)
        self.assertEqual(stg.param3, 'option3')
        self.assertTrue(np.array_equal(stg.param4, np.array([3.0, 4.0, 5.0])))

        # test updating parameters with wrong input
        # wrong input type for each parameter
        self.assertRaises(TypeError, stg.update_par_values, param1='wrong type')
        self.assertRaises(TypeError, stg.update_par_values, param2='wrong type')
        self.assertRaises(ValueError, stg.update_par_values, param3=123)  # wrong type
        self.assertRaises(ValueError, stg.update_par_values, param4='wrong type')  # wrong type
        # wrong input that go out of range both upper and lower bounds
        self.assertRaises(ValueError, stg.update_par_values, param1=101)  # out of range
        self.assertRaises(ValueError, stg.update_par_values, param1=0)
        self.assertRaises(ValueError, stg.update_par_values, param2=1.5)  # out of range
        self.assertRaises(ValueError, stg.update_par_values, param2=-0.1)
        self.assertRaises(ValueError, stg.update_par_values, param3='wrong option')  # out of range
        self.assertRaises(ValueError, stg.update_par_values, param4=np.array([6.0, 7.0, 8.0]))  # out of range
        self.assertRaises(ValueError, stg.update_par_values, param4=np.array([0.0, 0.0, 0.0]))  # out of range

    def test_stg_attribute_get_and_set(self):
        """ 测试策略属性的获取和设置 """
        stg = self.base_stg
        # print out all available parameters of the strategy:
        print(f'strategy parameters\n'
              f'stg_type: {stg.stg_type}\n'
              f'name: {stg.name}\n'
              f'description: {stg.description}\n'
              f'has_pars: {stg.has_pars}\n'
              f'pars: {stg.pars}\n'
              f'par_count: {stg.par_count}\n'
              f'par_values: {stg.par_values}\n'
              f'par_names: {stg.par_names}\n'
              f'par_types: {stg.par_types}\n'
              f'par_range: {stg.par_range}\n'
              f'opt_tag: {stg.opt_tag}\n'
              f'run_freq: {stg.run_freq}\n'
              f'run_timing: {stg.run_timing}\n'
              f'data_type_counts: {stg.data_type_count}\n'
              f'data_types: {stg.data_types}\n'
              f'data_type_ids: {stg.data_type_ids}\n'
              f'data_ids: {stg.data_ids}\n'
              f'data_names: {stg.data_names}\n'
              f'data_freqs: {stg.data_freqs}\n'
              f'data_ulc: {stg.data_ulc}\n'
              f'data_window_lengths: {stg.data_window_lengths}\n'
              f'window_lengths: {stg.window_lengths}\n'
              f'share_counts: {stg.share_count}\n'
              f'share_names: {stg.share_names}\n')

        stg.name = "CROSSLINE"
        stg.description = 'Moving average crossline strategy, determine long/short position according to the cross ' \
                        'point' \
                        ' of long and short term moving average prices '
        stg.opt_tag = 1
        stg.pars = {
            'param1': self.param1,
            'param2': self.param2,
        }
        stg.par_values = (55, 0.55)
        stg.run_freq = '5min'
        stg.run_timing = 'open'
        stg.data_types = [self.dtype_3, self.dtype_1, self.dtype_2]

        # print out all parameters again and assert their values:
        print(f'strategy parameters after setting new values\n'
              f'stg_type: {stg.stg_type}\n'
              f'name: {stg.name}\n'
              f'description: {stg.description}\n'
              f'has_pars: {stg.has_pars}\n'
              f'pars: {stg.pars}\n'
              f'par_count: {stg.par_count}\n'
              f'par_values: {stg.par_values}\n'
              f'par_names: {stg.par_names}\n'
              f'par_types: {stg.par_types}\n'
              f'par_range: {stg.par_range}\n'
              f'opt_tag: {stg.opt_tag}\n'
              f'run_freq: {stg.run_freq}\n'
              f'run_timing: {stg.run_timing}\n'
              f'data_type_counts: {stg.data_type_count}\n'
              f'data_types: {stg.data_types}\n'
              f'data_type_ids: {stg.data_type_ids}\n'
              f'data_ids: {stg.data_ids}\n'
              f'data_names: {stg.data_names}\n'
              f'data_freqs: {stg.data_freqs}\n'
              f'data_ulc: {stg.data_ulc}\n'
              f'data_window_lengths: {stg.data_window_lengths}\n'
              f'window_lengths: {stg.window_lengths}\n'
              f'share_counts: {stg.share_count}\n'
              f'share_names: {stg.share_names}\n')

        self.assertEqual(stg.name, "CROSSLINE")
        self.assertEqual(stg.description, 'Moving average crossline strategy, determine long/short '
                                          'position according to the cross '
                                          'point of long and short term moving average prices ')
        self.assertEqual(stg.has_pars, True)
        self.assertEqual(stg.par_count, 2)
        self.assertEqual(stg.par_values, (55, 0.55))
        self.assertEqual(stg.par_names, ['param1', 'param2'])
        self.assertEqual(stg.par_types, {'param1': 'int', 'param2': 'float'})
        self.assertEqual(stg.par_range, {'param1': (1, 100), 'param2': (0.0, 1.0)})
        self.assertEqual(stg.opt_tag, 1)
        self.assertEqual(stg.run_freq, '5min')
        self.assertEqual(stg.run_timing, 'open')
        self.assertEqual(stg.data_type_count, 3)
        self.assertEqual(stg.data_types, {'close_E_5min': self.dtype_3,
                                                 'close_E_d': self.dtype_1,
                                                 'close_E_h': self.dtype_2})
        self.assertEqual(stg.data_type_ids, ['close_E_5min', 'close_E_d', 'close_E_h'])
        self.assertEqual(stg.data_ids, ['close_E_5min', 'close_E_d', 'close_E_h'])
        self.assertEqual(stg.data_names, {'close_E_5min': 'close',
                                            'close_E_d': 'close',
                                            'close_E_h': 'close'})
        self.assertEqual(stg.data_freqs, {'close_E_5min': '5min',
                                            'close_E_d': 'd',
                                            'close_E_h': 'h'})
        self.assertEqual(stg.data_ulc, {'close_E_5min': False,
                                        'close_E_d': False,
                                        'close_E_h': False})
        self.assertEqual(stg.data_window_lengths, {'close_E_5min': 30,
                                                   'close_E_d': 30,
                                                   'close_E_h': 30})
        self.assertEqual(stg.window_lengths, {'close_E_5min': 30,
                                              'close_E_d': 30,
                                                    'close_E_h': 30})
        self.assertEqual(stg.share_count, 0)
        self.assertEqual(stg.share_names, [])
        # test clear our parameters
        stg.pars = {}

        self.assertEqual(stg.has_pars, False)
        self.assertEqual(stg.par_count, 0)
        self.assertEqual(stg.par_values, ())
        self.assertEqual(stg.par_names, [])
        self.assertEqual(stg.par_types, {})
        self.assertEqual(stg.par_range, {})

        # test clear our data types
        stg.data_types = []

        self.assertEqual(stg.data_type_count, 0)
        self.assertEqual(stg.data_types, {})
        self.assertEqual(stg.data_type_ids, [])
        self.assertEqual(stg.data_ids, [])
        self.assertEqual(stg.data_names, {})
        self.assertEqual(stg.data_freqs, {})
        self.assertEqual(stg.data_ulc, {})
        self.assertEqual(stg.data_window_lengths, {})
        self.assertEqual(stg.window_lengths, {})

    def test_methods(self):
        """ test all methods of strategy class"""
        stg = self.base_stg

        # test info method
        stg.info()
        stg.info(verbose=True)

        # test get_use_latest_data_cycle method
        self.assertEqual(stg.get_use_latest_data_cycle('close_E_d'), False)
        self.assertEqual(stg.get_use_latest_data_cycle('close_E_h'), False)
        self.assertEqual(stg.get_use_latest_data_cycle('close_E_5min'), False)
        self.assertEqual(stg.get_use_latest_data_cycle('close_E_15min'), False)
        self.assertEqual(stg.get_use_latest_data_cycle('close_E_w'), False)
        self.assertRaises(KeyError, stg.get_use_latest_data_cycle, 'wrong_id')

        # test get_data_ULC method
        self.assertEqual(stg.get_data_ULC('close_E_d'), False)
        self.assertEqual(stg.get_data_ULC('close_E_h'), False)
        self.assertEqual(stg.get_data_ULC('close_E_5min'), False)
        self.assertEqual(stg.get_data_ULC('close_E_15min'), False)
        self.assertEqual(stg.get_data_ULC('close_E_w'), False)
        self.assertRaises(KeyError, stg.get_data_ULC, 'wrong_id')

        # test get_window_length method
        self.assertEqual(stg.get_window_length('close_E_d'), 10)
        self.assertEqual(stg.get_window_length('close_E_h'), 20)
        self.assertEqual(stg.get_window_length('close_E_5min'), 30)
        self.assertEqual(stg.get_window_length('close_E_15min'), 40)
        self.assertEqual(stg.get_window_length('close_E_w'), 50)
        self.assertRaises(KeyError, stg.get_window_length, 'wrong_id')

        # test get_data_name method
        self.assertEqual(stg.get_data_name('close_E_d'), 'close')
        self.assertEqual(stg.get_data_name('close_E_h'), 'close')
        self.assertEqual(stg.get_data_name('close_E_5min'), 'close')
        self.assertEqual(stg.get_data_name('close_E_15min'), 'close')
        self.assertEqual(stg.get_data_name('close_E_w'), 'close')
        self.assertRaises(KeyError, stg.get_data_name, 'wrong_id')

        # test update_data_window method
        

    def test_rule_iterator(self):
        """测试rule_iterator类型策略"""
        stg = TestLSStrategy()
        self.assertIsInstance(stg, BaseStrategy)
        self.assertIsInstance(stg, RuleIterator)
        stg_pars = {'000100': (5, 10),
                    '000200': (5, 10),
                    '000300': (5, 6)}
        stg.set_pars(stg_pars)
        history_data = self.hp1.values[:, :-1]
        history_data_rolling_window = rolling_window(history_data, stg.window_length, 1)

        # test strategy generate with only hist_data
        print(f'test strategy generate with only hist_data')
        output = stg.generate(hist_data=history_data_rolling_window,
                              data_idx=np.arange(len(history_data_rolling_window)))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        lsmask = np.array([[0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 0.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 0.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0],
                           [0.0, 1.0, 1.0]])
        self.assertEqual(output.shape, lsmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {lsmask[i]}')
        self.assertTrue(np.allclose(output, lsmask, equal_nan=True))

        # test strategy generate with history data and reference_data
        print(f'\ntest strategy generate with reference_data')
        ref_data = self.test_ref_data[0, :, :]
        ref_rolling_window = rolling_window(ref_data, stg.window_length, 0)
        output = stg.generate(hist_data=history_data_rolling_window,
                              ref_data=ref_rolling_window,
                              data_idx=np.arange(len(history_data_rolling_window)))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        lsmask = np.array([[1.0, 0.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 0.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 1.0],
                           [1.0, 1.0, 1.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [1.0, 1.0, 1.0]])
        self.assertEqual(output.shape, lsmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {lsmask[i]}')
        self.assertTrue(np.allclose(output, lsmask, equal_nan=True))

        # test strategy generate with trade_data
        print(f'\ntest strategy generate with trade_data')
        output = []
        trade_data = np.empty(shape=(3, 5))  # 生成的trade_data符合5行
        trade_data.fill(np.nan)
        recent_prices = np.zeros(shape=(3,))
        for step in range(len(history_data_rolling_window)):
            output.append(
                    stg.generate(
                            hist_data=history_data_rolling_window,
                            trade_data=trade_data,
                            data_idx=step
                    )
            )
            current_prices = history_data_rolling_window[step, :, -1, 0]
            current_signals = output[-1]
            recent_prices = np.where(current_signals == 1., current_prices, recent_prices)
            trade_data[:, 4] = recent_prices
        output = np.array(output, dtype='float')

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        lsmask = np.array([[1.0, 1.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 1.0],
                           [1.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [1.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.0, 0.0]])
        self.assertEqual(output.shape, lsmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {lsmask[i]}')
        self.assertTrue(np.allclose(output, lsmask, equal_nan=True))

    def test_general_strategy(self):
        """ 测试第一种基础策略类General Strategy"""
        # test strategy with only history data
        stg = TestSelStrategy()
        self.assertIsInstance(stg, BaseStrategy)
        self.assertIsInstance(stg, GeneralStg)
        stg_pars = ()
        stg.set_pars(stg_pars)
        history_data = self.hp1['high, low, close', :, :-1]
        history_data_rolling_window = rolling_window(history_data, stg.window_length, 1)

        output = stg.generate(hist_data=history_data_rolling_window,
                              data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test strategy with history data and reference data
        print(f'\ntest strategy generate with reference_data')
        ref_data = self.test_ref_data[0, :, :]
        ref_rolling_window = rolling_window(ref_data, stg.window_length, 0)
        output = stg.generate(hist_data=history_data_rolling_window,
                              ref_data=ref_rolling_window,
                              data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])
        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test strategy generate with trade_data
        print(f'\ntest strategy generate with trade_data')
        output = []
        trade_data = np.empty(shape=(3, 5))  # 生成的trade_data符合5行
        trade_data.fill(np.nan)
        recent_prices = np.zeros(shape=(3,))
        prev_signals = np.zeros(shape=(3,))
        for step in range(len(history_data_rolling_window)):
            output.append(
                    stg.generate(
                            hist_data=history_data_rolling_window,
                            trade_data=trade_data,
                            data_idx=step
                    )
            )
            current_prices = history_data_rolling_window[step, :, -1, 2]
            current_signals = output[-1]
            recent_prices = np.where(current_signals != prev_signals, current_prices, recent_prices)
            trade_data[:, 4] = recent_prices
            prev_signals = current_signals
        output = np.array(output, dtype='float')

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.33333, 0.33333, 0.33333],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0, 0.5],
                            [0, 0.5, 0.5],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0, 0.5],
                            [0.5, 0, 0.5],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0.5, 0, 0.5],
                            [0, 0.5, 0.5],
                            [0, 0.5, 0.5],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5],
                            [0.5, 0, 0.5],
                            [0.5, 0.5, 0],
                            [0.5, 0.5, 0],
                            [0, 0.5, 0.5]])
        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'step: {i}:\n'
                  f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, atol=0.001, equal_nan=True))

    def test_factor_sorter(self):
        """Test Factor Sorter 策略, test all built-in strategy parameters"""
        print(f'\ntest strategy generate with only history data')
        stg = SelectingAvgIndicator()
        self.assertIsInstance(stg, BaseStrategy)
        self.assertIsInstance(stg, FactorSorter)
        stg_pars = (False, 'even', 'greater', 0, 0, 0.67)
        stg.set_pars(stg_pars)
        stg.window_length = 5
        stg.data_freq = 'd'
        stg.run_freq = '10d'
        stg.sort_ascending = False
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.max_sel_count = 0.67
        # test additional FactorSorter properties
        self.assertEqual(stg_pars, (False, 'even', 'greater', 0, 0, 0.67))
        self.assertEqual(stg.window_length, 5)
        self.assertEqual(stg.data_freq, 'd')
        self.assertEqual(stg.run_freq, '10d')
        self.assertEqual(stg.sort_ascending, False)
        self.assertEqual(stg.condition, 'greater')
        self.assertEqual(stg.lbound, 0)
        self.assertEqual(stg.ubound, 0)
        self.assertEqual(stg.max_sel_count, 0.67)

        history_data = self.hp2.values[:, :-1]
        hist_data_rolling_window = rolling_window(history_data, window=stg.window_length, axis=1)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))

        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(output.shape, (45, 3))

        selmask = np.array([[0.0, 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.0, 1.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        print(pd.DataFrame(output, index=self.hp1.hdates[5:], columns=self.hp1.shares))
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test single factor, get mininum factor
        stg_pars = (True, 'even', 'less', 1, 1, 0.67)
        stg.sort_ascending = True
        stg.condition = 'less'
        stg.lbound = 1
        stg.ubound = 1
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0.5, 0.5, 0.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.0, 1.0],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.0, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        print(pd.DataFrame(output, index=self.hp1.hdates[5:], columns=self.hp1.shares))
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test single factor, get max factor in linear weight
        stg_pars = (False, 'linear', 'greater', 0, 0, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'linear'
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0.0, 0.33333333, 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.66666667, 0.33333333],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.0, 0.33333333, 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.33333333, 0., 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.33333333, 0., 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.33333333, 0.66666667, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, equal_nan=True))

        # test single factor, get max factor in linear weight
        stg_pars = (False, 'distance', 'greater', 0, 0, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'distance'
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0., 0.08333333, 0.91666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.91666667, 0.08333333],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.08333333, 0., 0.91666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.08333333, 0., 0.91666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.08333333, 0.91666667, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, 0.001, equal_nan=True))

        # test single factor, get max factor in proportion weight
        stg_pars = (False, 'proportion', 'greater', 0, 0, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'proportion'
        stg.condition = 'greater'
        stg.lbound = 0
        stg.ubound = 0
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0., 0.4, 0.6],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.6, 0.4],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.33333333, 0., 0.66666667],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.25, 0., 0.75],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.375, 0.625, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, 0.001, equal_nan=True))

        # test single factor, get max factor in linear weight, threshold 0.2
        stg_pars = (False, 'even', 'greater', 0.2, 0.2, 0.67)
        stg.sort_ascending = False
        stg.weighting = 'even'
        stg.condition = 'greater'
        stg.lbound = 0.2
        stg.ubound = 0.2
        stg.set_pars(stg_pars)
        print(f'Start to test financial selection parameter {stg_pars}')

        output = stg.generate(hist_data=hist_data_rolling_window, data_idx=np.array([0, 6, 14, 21, 28, 36, 42]))
        selmask = np.array([[0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0.5, 0.5],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0., 0., 1.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan],
                            [0.5, 0.5, 0.],
                            [np.nan, np.nan, np.nan],
                            [np.nan, np.nan, np.nan]])

        self.assertEqual(output.shape, selmask.shape)
        for i in range(len(output)):
            print(f'output:    {output[i]}\n'
                  f'selmask:   {selmask[i]}')
        self.assertTrue(np.allclose(output, selmask, 0.001, equal_nan=True))

        print(f'\ntest financial generate with reference data')
        # to be added


if __name__ == '__main__':
    unittest.main()