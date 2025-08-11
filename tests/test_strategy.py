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


if __name__ == '__main__':
    unittest.main()