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


param1 = Parameter(
        name='param1',
        par_type='int',
        par_range=(1, 100),
        value=50,
)

param2 = Parameter(
        name='param2',
        par_type='float',
        par_range=(0.0, 1.0),
        value=0.5,
)

param3 = Parameter(
        name='param3',
        par_type='enum',
        par_range=('option1', 'option2', 'option3'),
        value='option1',
)

param4 = Parameter(
        name='param4',
        par_type='array[3,]',
        par_range=(1.0, 5.0),
        value=np.array([1.0, 2.0, 3.0]),
)

dtype_1 = DataType(
        name='close',
        freq='d',
        asset_type='E',
)

dtype_2 = DataType(
        name='close',
        freq='h',
        asset_type='E',
)

dtype_3 = DataType(
        name='close',
        freq='5min',
        asset_type='E',
)

dtype_4 = DataType(
        name='close',
        freq='15min',
        asset_type='E',
)

dtype_5 = DataType(
        name='close',
        freq='w',
        asset_type='E',
)


# 创建三个测试交易策略类，用于测试
class GenStg(GeneralStg):
    """第一个测试交易策略类，继承自GeneralStg

    包含两个可调参数: `param1` 和 `param2`，用于测试参数传递和使用。
    使用三种不同的数据类型: 'price@5minx30', 'volume@hx10', 'indicator@dx5'，用于测试数据类型的处理。
    """
    def __init__(self, par_values=None):
        super().__init__(
                name='test_gen',
                description='test general strategy',
                run_freq='d',
                run_timing='close',
                pars=[param1, param2],
                stg_type='general',
                data_types={'dt1': dtype_1, 'dt2': dtype_3},
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


class TestStrategy(unittest.TestCase):
    def test_creation(self):
        """ test creation of strategy objects"""
        stg = BaseStrategy(
                name='TestStrategy',
                run_freq='d',
                run_timing='close',
                pars=[param1, param2, param3, param4],
                data_types=[dtype_1, dtype_2, dtype_3, dtype_4, dtype_5],
                use_latest_data_cycle=False,
                window_length=[10, 20, 30, 40, 50],
        )

        self.assertIsInstance(stg, BaseStrategy)
        self.assertEqual(stg.name, 'TestStrategy')
        self.assertEqual(stg.run_freq, 'd')
        self.assertEqual(stg.run_timing, 'close')
        stg.info()
        stg.info(verbose=True)

    def test_properties(self):

        stg = BaseStrategy(
                name='TestStrategy',
                run_freq='d',
                run_timing='close',
                pars=[param1, param2, param3, param4],
                data_types=[dtype_1, dtype_2, dtype_3, dtype_4
                            , dtype_5],
                use_latest_data_cycle=False,
        )

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

        stg = BaseStrategy(
                name='TestStrategy',
                run_freq='d',
                run_timing='close',
                pars=[param1, param2, param3, param4],
                data_types=[dtype_1, dtype_2, dtype_3, dtype_4, dtype_5],
                use_latest_data_cycle=False,
                window_length=[10, 20, 30, 40, 50],
        )

        # test updating parameters
        stg.update_par_values((75, 0.75, 'option2', np.array([2.0, 3.0, 4.0])))
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

    def test_general_stg(self):
        pass

    def test_stg_parameter_setting(self):
        """ test setting parameters of strategies
        test the method set_parameters

        :return:
        """
        op = qt.Operator(strategies='dma, all, sellrate')
        print(op.strategies, '\n', [qt.built_in.DMA, qt.built_in.SelectingAll, qt.built_in.SellRate])
        print(f'info of Timing strategy in new op: \n{op.strategies[0].info()}')
        # TODO: allow set_parameters to a list of strategies or str-listed strategies
        # TODO: allow set_parameters to all strategies of specific bt price type
        print(f'Set up strategy parameters by strategy id')
        op.set_parameter('dma',
                         opt_tag=1,
                         par_range=((5, 10), (5, 15), (5, 15)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('dma',
                         pars=(5, 10, 5))
        op.set_parameter('all',
                         window_length=20)
        op.set_parameter('all', run_timing='close')
        print(f'Can also set up strategy parameters by strategy index')
        op.set_parameter(2, run_timing='open')
        op.set_parameter(2,
                         opt_tag=1,
                         pars=(9, -0.09),
                         window_length=10)
        self.assertEqual(op.strategies[0].par_values, (5, 10, 5))
        self.assertEqual(op.strategies[0].par_range, ((5, 10), (5, 15), (5, 15)))
        self.assertEqual(op.strategies[2].par_values, (9, -0.09))
        self.assertEqual(op.op_data_freq, 'd')
        self.assertEqual(op.op_data_types, ['close', 'high', 'open'])
        self.assertEqual(op.opt_space_par,
                         ([(5, 10), (5, 15), (5, 15), (1, 100), (-0.5, 0.5)],
                          ['int', 'int', 'int', 'int', 'float']))
        self.assertEqual(op.max_window_length, 20)
        print(f'KeyError will be raised if wrong strategy id is given')
        self.assertRaises(KeyError, op.set_parameter, stg_id='t-1', pars=(1, 2))
        self.assertRaises(KeyError, op.set_parameter, stg_id='wrong_input', pars=(1, 2))
        print(f'ValueError will be raised if parameter can be set')
        self.assertRaises(ValueError, op.set_parameter, stg_id=0, pars=('wrong input', 'wrong input'))
        # test blenders of different price types
        # test setting blenders to different price types

        # self.assertEqual(a_to_sell.get_blender('close'), 'str-1.2')
        self.assertEqual(op.strategy_groups, ['close', 'open'])
        op.set_blender('s0 and s1 or s2', 'open')
        self.assertEqual(op.get_blender('open'), ['or', 's2', 'and', 's1', 's0'])
        op.set_blender('s0 or s1 and s2', 'close')
        self.assertEqual(op.get_blender(), {'close': ['or', 'and', 's2', 's1', 's0'],
                                            'open':  ['or', 's2', 'and', 's1', 's0']})

        self.assertEqual(op.opt_space_par,
                         ([(5, 10), (5, 15), (5, 15), (1, 100), (-0.5, 0.5)],
                          ['int', 'int', 'int', 'int', 'float']))
        self.assertEqual(op.opt_tags, [1, 0, 1])

    def test_set_opt_par(self):
        """ test setting opt pars in batch"""
        print(f'--------- Testing setting Opt Pars: set_opt_par -------')
        op = qt.Operator('dma, random, crossline')
        op.set_parameter('dma',
                         opt_tag=1,
                         par_range=((5, 10), (5, 15), (5, 15)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('dma',
                         pars=(5, 10, 5))
        self.assertEqual(op.strategies[0].par_values, (5, 10, 5))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (35, 120, 0.02))
        self.assertEqual(op.opt_tags, [1, 0, 0])
        op.set_opt_par((5, 12, 9))
        self.assertEqual(op.strategies[0].par_values, (5, 12, 9))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (35, 120, 0.02))

        op.set_parameter('crossline',
                         opt_tag=1,
                         par_range=((5, 10), (5, 35), (0, 1)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('crossline',
                         pars=(5, 10, 0.1))
        self.assertEqual(op.opt_tags, [1, 0, 1])
        op.set_opt_par((5, 12, 9, 8, 26, 0.09))
        self.assertEqual(op.strategies[0].par_values, (5, 12, 9))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (8, 26, 0.09))

        op.set_opt_par((9, 200, 155, 8, 26, 0.09, 5, 12, 9))
        self.assertEqual(op.strategies[0].par_values, (9, 200, 155))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (8, 26, 0.09))

        # test set_opt_par when opt_tag is set to be 2 (enumerate type of parameters)
        op.set_parameter('crossline',
                         opt_tag=2,
                         par_range=((5, 10), (5, 35), (5, 15)),
                         window_length=10,
                         strategy_data_types=['close', 'open', 'high'])
        op.set_parameter('crossline',
                         pars=(5, 10, 5))
        self.assertEqual(op.opt_tags, [1, 0, 2])
        self.assertEqual(op.strategies[0].par_values, (9, 200, 155))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (5, 10, 5))
        op.set_opt_par((5, 12, 9, (8, 26, 9)))
        self.assertEqual(op.strategies[0].par_values, (5, 12, 9))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (8, 26, 9))

        # Test Errors
        # op.set_opt_par主要在优化过程中自动生成，已经保证了参数的正确性，因此不再检查参数正确性

    def test_stg_attribute_get_and_set(self):
        self.stg = qt.built_in.CROSSLINE()
        self.stg_type = 'RULE-ITER'
        self.stg_name = "CROSSLINE"
        self.stg_text = 'Moving average crossline strategy, determine long/short position according to the cross ' \
                        'point' \
                        ' of long and short term moving average prices '
        self.pars = (35, 120, 0.02)
        self.par_boes = [(10, 250), (10, 250), (0, 0.1)]
        self.par_count = 3
        self.par_types = ['int', 'int', 'float']
        self.opt_tag = 0
        self.data_types = ['close']
        self.data_freq = 'd'
        self.sample_freq = 'd'
        self.window_length = 270

        self.assertEqual(self.stg.stg_type, self.stg_type)
        self.assertEqual(self.stg.name, self.stg_name)
        self.assertEqual(self.stg.description, self.stg_text)
        self.assertEqual(self.stg.par_values, self.pars)
        self.assertEqual(self.stg.par_types, self.par_types)
        self.assertEqual(self.stg.par_range, self.par_boes)
        self.assertEqual(self.stg.par_count, self.par_count)
        self.assertEqual(self.stg.opt_tag, self.opt_tag)
        self.assertEqual(self.stg.data_freq, self.data_freq)
        self.assertEqual(self.stg.run_freq, self.sample_freq)
        self.assertEqual(self.stg.data_types, self.data_types)
        self.assertEqual(self.stg.window_length, self.window_length)
        self.stg.name = 'NEW NAME'
        self.stg.description = 'NEW TEXT'
        self.assertEqual(self.stg.name, 'NEW NAME')
        self.assertEqual(self.stg.description, 'NEW TEXT')
        self.stg.par_values = (10, 20, 0.03)
        self.assertEqual(self.stg.par_values, (10, 20, 0.03))
        self.stg.par_count = 3
        self.assertEqual(self.stg.par_count, 3)
        self.stg.par_range = [(1, 10), (1, 10), (1, 10), (1, 10)]
        self.assertEqual(self.stg.par_range, [(1, 10), (1, 10), (1, 10), (1, 10)])
        self.stg.par_types = ['float', 'float', 'int', 'enum']
        self.assertEqual(self.stg.par_types, ['float', 'float', 'int', 'enum'])
        self.stg.par_types = 'float, float, int, float'
        self.assertEqual(self.stg.par_types, ['float', 'float', 'int', 'float'])
        self.stg.data_types = 'close, open'
        self.assertEqual(self.stg.data_types, ['close', 'open'])
        self.stg.data_types = ['close', 'high', 'low']
        self.assertEqual(self.stg.data_types, ['close', 'high', 'low'])
        self.stg.data_freq = 'w'
        self.assertEqual(self.stg.data_freq, 'w')
        self.stg.window_length = 300
        self.assertEqual(self.stg.window_length, 300)

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

    def test_general_strategy2(self):
        """ 测试第二种general strategy通用策略类型"""
        # test strategy with only historical data
        stg = TestSigStrategy()
        stg_pars = (0.2, 0.02, -0.02)
        stg.set_pars(stg_pars)
        history_data = self.hp1['close, open, high, low', :, 4:50]
        history_data_rolling_window = rolling_window(history_data, stg.window_length, 1)

        # test generate signal in real time mode:
        output = []
        for step in [0, 3, 5, 7, 10]:
            output.append(stg.generate(hist_data=history_data_rolling_window, data_idx=step))
        sigmatrix = np.array([[0.0, 1.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0]])
        for signal, target in zip(output, sigmatrix):
            self.assertIsInstance(signal, np.ndarray)
            self.assertEqual(signal.shape, (3,))
            self.assertTrue(np.allclose(signal, target))

        # test generate signal in batch mode:
        output = stg.generate(hist_data=history_data_rolling_window,
                              data_idx=np.arange(len(history_data_rolling_window)))

        sigmatrix = np.array([[0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, -1.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [-1.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0]])

        side_by_side_array = [[i, out_line, sig_line]
                                       for
                                       i, out_line, sig_line
                                       in zip(range(len(output)), output, sigmatrix)]
        # side_by_side_array = np.array(side_by_side_array)
        print(f'output and signal matrix lined up side by side is \n'
              f'{side_by_side_array}')
        self.assertEqual(sigmatrix.shape, output.shape)
        self.assertTrue(np.allclose(np.array(output), sigmatrix))

        # test strategy with also reference data
        print(f'\ntest strategy generate with reference_data')
        stg_pars = (0.3, 0.02, -0.02)
        stg.set_pars(stg_pars)
        history_data = self.hp1['close, open, high, low', :, 4:50]
        history_data_rolling_window = rolling_window(history_data, stg.window_length, 1)
        reference_data = self.test_ref_data2[0, 4:50, :]
        ref_rolling_windows = rolling_window(reference_data, stg.window_length, 0)

        # test generate signal in real time mode:
        output = []
        for step in [0, 3, 5, 7, 10]:
            output.append(stg.generate(
                    hist_data=history_data_rolling_window,
                    ref_data=ref_rolling_windows,
                    data_idx=step
            ))
        sigmatrix = np.array([[0.0, 1.0, 0.0],
                              [1.0, -1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [-1.0, 1.0, 0.0]])
        for signal, target in zip(output, sigmatrix):
            self.assertIsInstance(signal, np.ndarray)
            self.assertEqual(signal.shape, (3,))
            self.assertTrue(np.allclose(signal, target))

        # test generate signal in batch mode:
        output = stg.generate(
                hist_data=history_data_rolling_window,
                ref_data=ref_rolling_windows,
                data_idx=np.arange(len(history_data_rolling_window))
        )

        sigmatrix = np.array([[0.0, 1.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, -1.0, 0.0],
                              [1.0, -1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [-1.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, -1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, -1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [1.0, 0.0, 1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [-1.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 1.0],
                              [0.0, 1.0, 0.0],
                              [1.0, 0.0, 0.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 0.0, 1.0],
                              [0.0, 0.0, 0.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 0.0, -1.0],
                              [0.0, 1.0, 0.0],
                              [0.0, 1.0, 0.0]])

        side_by_side_array = [[i, out_line == sig_line, out_line, sig_line]
                                       for
                                       i, out_line, sig_line
                                       in zip(range(len(output)), output, sigmatrix)]
        # side_by_side_array = np.array(side_by_side_array)
        print(f'output and signal matrix lined up side by side is \n'
              f'{side_by_side_array}')
        self.assertEqual(sigmatrix.shape, output.shape)
        self.assertTrue(np.allclose(np.array(output), sigmatrix, equal_nan=True))

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