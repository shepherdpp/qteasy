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
from qteasy.utilfuncs import rolling_window


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
                par_range=(0.0, 10.),
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
                window_length=[3, 7, 5, 8, 6],
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

            def __init__(self, par_values: tuple = None):
                super().__init__(
                        name='test_gen',
                        description='test general strategy',
                        run_freq='d',
                        run_timing='close',
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

            param1 = self.param1
            param2 = self.param2
            dtype_1 = self.dtype_1
            dtype_3 = self.dtype_3

            def __init__(self, par_values=None, **kwargs):
                super().__init__(
                        name='test_factor_sorter',
                        description='test factor sorter strategy',
                        run_freq='d',
                        run_timing='close',
                        # TODO: user-defined parameter names should also be allowed
                        pars=[self.param1, self.param2],
                        # TODO: user-defined dtype names should be allowed using {name: Dtype} form
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

            param1 = self.param1
            param2 = self.param2
            dtype_1 = self.dtype_1
            dtype_3 = self.dtype_3

            def __init__(self, par_values=None):
                super().__init__(
                        name='test_rule_iterator',
                        description='test rule iterator strategy',
                        run_freq='d',
                        run_timing='close',
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
        self.gen_stg = GenStg(par_values=(50, 0.5))

        self.factor_sorter_stg = FactorSorterStg(
                par_values=(10, 0.6)
        )

        self.rule_iterator_stg = RuleIteratorStg()

        # data used to create windows
        self.test_data = dict(
                close_E_d=np.array([[0.994, 0.412, 0.876],
                                    [1.117, 1.257, 1.447],
                                    [2.315, 2.08, 2.799],
                                    [3.704, 3.87, 3.62],
                                    [4.091, 4.127, 4.218],
                                    [5.177, 5.337, 5.294],
                                    [6.24, 6.254, 6.626],
                                    [7.552, 7.446, 7.739],
                                    [8.754, 8.192, 8.65],
                                    [9.877, 9.685, 9.885],
                                    [10.556, 10.774, 10.25],
                                    [11.167, 11.026, 11.999],
                                    [12.58, 12.236, 12.307],
                                    [13.599, 13.797, 13.155],
                                    [14.921, 14.938, 14.481],
                                    [15.281, 15.604, 15.348],
                                    [16.062, 16.559, 16.88],
                                    [17.39, 17.247, 17.393],
                                    [18.902, 18.344, 18.878],
                                    [19.127, 19.099, 19.396],
                                    [20.332, 20.854, 20.131],
                                    [21.482, 21.229, 21.578],
                                    [22.435, 22.952, 22.289],
                                    [23.605, 23.377, 23.311],
                                    [24.676, 24.23, 24.839]]),
                close_E_h=np.array([[0.593, 0.82, 0.13],
                                    [1.343, 1.253, 1.198],
                                    [2.732, 2.43, 2.873],
                                    [3.539, 3.9, 3.725],
                                    [4.394, 4.374, 4.294],
                                    [5.898, 5.237, 5.132],
                                    [6.447, 6.394, 6.976],
                                    [7.14, 7.871, 7.544],
                                    [8.816, 8.267, 8.663],
                                    [9.108, 9.517, 9.412],
                                    [10.754, 10.051, 10.161],
                                    [11.798, 11.445, 11.558],
                                    [12.103, 12.778, 12.4],
                                    [13.564, 13.616, 13.387],
                                    [14.858, 14.465, 14.478],
                                    [15.973, 15.728, 15.84],
                                    [16.733, 16.323, 16.027],
                                    [17.705, 17.642, 17.954],
                                    [18.808, 18.995, 18.233],
                                    [19.418, 19.02, 19.943],
                                    [20.712, 20.348, 0.239],
                                    [21.569, 21.743, 1.552],
                                    [22.931, 22.382, 2.153],
                                    [23.571, 23.224, 3.841],
                                    [24.853, 24.294, 4.279]]),
                close_E_5min=np.array([[0.97, 0.892, 0.784],
                                       [1.526, 1.455, 1.606],
                                       [2.509, 2.662, 2.306],
                                       [3.882, 3.308, 3.838],
                                       [4.766, 4.977, 4.34],
                                       [5.708, 5.401, 5.724],
                                       [6.744, 6.793, 6.576],
                                       [7.32, 7.943, 7.124],
                                       [8.906, 8.529, 8.188],
                                       [9.742, 9.037, 9.896],
                                       [10.576, 10.528, 10.546],
                                       [11.267, 11.595, 11.761],
                                       [12.747, 12.589, 12.211],
                                       [13.071, 13.948, 13.95],
                                       [14.499, 14.872, 14.306],
                                       [15.521, 15.553, 15.939],
                                       [16.383, 16.966, 16.419],
                                       [17.322, 17.845, 17.583],
                                       [18.631, 18.327, 18.274],
                                       [19.192, 19.413, 19.882],
                                       [20.533, 20.566, 20.406],
                                       [21.585, 21.583, 21.433],
                                       [22.381, 22.428, 22.356],
                                       [23.833, 23.275, 23.104],
                                       [24.514, 24.537, 24.06]]),
                close_E_15min=np.array([[0.704, 0.179, 0.9],
                                        [0.882, 0.831, 1.206],
                                        [0.61, 1.024, 1.473],
                                        [0.797, 1.126, 1.37],
                                        [1.632, 1.767, 1.102],
                                        [1.802, 1.893, 1.783],
                                        [1.861, 1.88, 1.854],
                                        [2.515, 2.584, 2.603],
                                        [2.326, 2.737, 2.25],
                                        [2.55, 2.545, 2.654],
                                        [3.418, 2.655, 2.9],
                                        [2.924, 3.673, 3.706],
                                        [3.653, 3.95, 3.319],
                                        [3.314, 4.181, 4.022],
                                        [3.523, 4.29, 4.267],
                                        [4.598, 4.282, 3.935],
                                        [4.08, 4.105, 4.498],
                                        [4.757, 5.032, 4.547],
                                        [4.529, 4.91, 4.535],
                                        [5.229, 5.288, 5.085],
                                        [5.641, 5.074, 5.016],
                                        [6.222, 6.181, 5.866],
                                        [6.025, 5.769, 5.506],
                                        [6.365, 6.512, 6.316],
                                        [6.104, 6.982, 6.779],
                                        [6.258, 6.899, 6.395],
                                        [7.316, 7.388, 6.71],
                                        [7.377, 7.422, 7.299],
                                        [7.701, 7.688, 7.205],
                                        [7.312, 7.975, 7.673],
                                        [8.476, 8.472, 8.487],
                                        [8.591, 8.63, 7.768],
                                        [8.726, 8.918, 8.23],
                                        [8.554, 8.39, 8.686],
                                        [8.946, 8.794, 8.688],
                                        [8.75, 9.532, 9.151],
                                        [9.551, 9.622, 9.375],
                                        [9.604, 9.958, 10.159],
                                        [9.817, 9.933, 10.225],
                                        [10.231, 9.784, 10.579],
                                        [10.947, 10.895, 10.823],
                                        [10.324, 10.699, 10.652],
                                        [11.19, 10.514, 10.977],
                                        [10.878, 11.261, 11.267],
                                        [11.92, 11.524, 11.359],
                                        [12.032, 12.097, 11.81],
                                        [11.901, 12.379, 12.362],
                                        [12.067, 12.299, 11.844],
                                        [12.117, 12.482, 12.886],
                                        [12.759, 12.631, 12.658],
                                        [13.363, 12.705, 12.758],
                                        [13.507, 13.302, 13.375],
                                        [13.691, 13.421, 13.15],
                                        [13.913, 13.977, 14.13],
                                        [13.812, 14.027, 14.423],
                                        [14.148, 13.96, 13.978],
                                        [14.363, 14.556, 14.241],
                                        [14.624, 15.074, 15.048],
                                        [14.814, 14.968, 15.132],
                                        [14.756, 15.669, 15.643],
                                        [15.564, 15.386, 15.105],
                                        [15.624, 16.184, 15.963],
                                        [15.629, 16.339, 15.819],
                                        [16.567, 16.013, 16.575],
                                        [16.24, 16.318, 16.011],
                                        [16.881, 16.95, 16.276],
                                        [16.911, 16.986, 17.131],
                                        [16.986, 17.052, 17.523],
                                        [17.389, 17.634, 17.998],
                                        [17.404, 18.193, 17.411],
                                        [17.633, 18.462, 18.201],
                                        [18.316, 18.651, 18.633],
                                        [18.941, 18.129, 18.014],
                                        [18.834, 18.3, 18.316],
                                        [19.303, 19.457, 19.35],
                                        [18.842, 19.071, 19.253],
                                        [19.528, 19.033, 19.273],
                                        [19.385, 19.665, 20.08],
                                        [19.936, 19.765, 20.262],
                                        [20.512, 20.441, 20.379],
                                        [20.018, 20.994, 20.374],
                                        [20.35, 20.754, 20.633],
                                        [21.176, 21.46, 20.546],
                                        [20.934, 21.328, 21.421],
                                        [21.414, 21.486, 21.426],
                                        [21.352, 21.786, 21.56],
                                        [21.552, 22.29, 21.921],
                                        [22.095, 21.885, 22.069],
                                        [22.795, 22.686, 22.516],
                                        [22.594, 23.153, 22.951],
                                        [22.87, 23.063, 22.501],
                                        [23.224, 23.51, 23.647],
                                        [23.048, 23.83, 23.679],
                                        [23.733, 23.355, 23.633],
                                        [23.658, 23.856, 23.99],
                                        [24.408, 24.181, 23.931],
                                        [24.716, 24.531, 24.268],
                                        [25.195, 24.866, 24.897],
                                        [25.384, 24.922, 25.486],
                                        [25.144, 25.661, 25.176]]),
                close_E_w=np.array([[0.134, 0.207, 0.095],
                                    [1.015, 0.591, 0.615],
                                    [1.255, 0.85, 0.992],
                                    [1.56, 1.107, 1.132],
                                    [1, 1.111, 1.224],
                                    [1.396, 1.325, 1.72],
                                    [2.414, 1.651, 2.119],
                                    [2.497, 2.406, 2.44],
                                    [2.04, 2.279, 2.832],
                                    [2.317, 2.473, 3.226],
                                    [2.825, 2.836, 2.73],
                                    [3.019, 3.574, 3.335],
                                    [3.306, 3.45, 3.36],
                                    [3.295, 3.401, 3.63],
                                    [3.639, 4.088, 4.026],
                                    [4.341, 4.214, 4.059],
                                    [4.834, 4.739, 4.775],
                                    [4.952, 5.152, 4.537],
                                    [4.896, 4.833, 4.583],
                                    [4.877, 5.266, 5.092],
                                    [5.47, 5.128, 5.494],
                                    [6.169, 5.552, 5.914],
                                    [5.799, 5.543, 5.553],
                                    [6.7, 5.976, 6.339],
                                    [6.862, 6.864, 6.431],
                                    [6.35, 7.196, 6.714],
                                    [6.952, 6.798, 6.641],
                                    [7.043, 7.416, 7.084],
                                    [7.162, 7.636, 7.993],
                                    [7.736, 8.095, 7.391],
                                    [8.293, 8.066, 7.843],
                                    [7.765, 7.795, 8.341],
                                    [8.216, 8.063, 8.15],
                                    [8.832, 8.347, 8.769],
                                    [9.405, 8.91, 9.19],
                                    [8.936, 9.377, 9.006],
                                    [9.9, 9.414, 9.804],
                                    [10.249, 10.085, 9.407],
                                    [9.777, 9.765, 10.366],
                                    [10.239, 10.05, 10.212],
                                    [10.011, 10.026, 10.426],
                                    [10.269, 11.219, 10.592],
                                    [10.834, 11.453, 11.207],
                                    [10.833, 11.703, 11.019],
                                    [11.687, 11.513, 11.004],
                                    [11.782, 11.565, 11.978],
                                    [12.149, 12.344, 12.271],
                                    [12.119, 12.728, 12.153],
                                    [12.659, 12.777, 12.797],
                                    [12.456, 13.043, 13.096],
                                    [12.896, 12.598, 12.665],
                                    [12.827, 13.557, 13.685],
                                    [13.544, 13.513, 13.874],
                                    [13.768, 13.322, 13.779],
                                    [13.916, 13.816, 13.701],
                                    [14.616, 13.817, 14.543],
                                    [14.917, 14.383, 14.929],
                                    [14.908, 14.919, 14.6],
                                    [14.982, 15.08, 14.569],
                                    [15.524, 15.283, 15.204],
                                    [15.17, 15.168, 15.544],
                                    [15.305, 16.242, 15.304],
                                    [15.857, 16.32, 16.169],
                                    [16.513, 16.501, 16.436],
                                    [16.348, 16.775, 16.457],
                                    [17.06, 16.416, 16.727],
                                    [16.765, 16.743, 17.164],
                                    [16.781, 17.367, 17.243],
                                    [17.276, 17.242, 17.586],
                                    [17.417, 17.519, 17.352],
                                    [17.632, 17.625, 17.965],
                                    [18.121, 17.759, 18.735],
                                    [18.433, 18.643, 18.416],
                                    [18.696, 19.104, 19.131],
                                    [18.568, 18.507, 18.979],
                                    [19.406, 19.572, 19.007],
                                    [19.416, 19.216, 19.95],
                                    [19.894, 19.411, 19.353],
                                    [20.363, 19.79, 19.849],
                                    [20.131, 19.823, 19.844],
                                    [20.187, 20.775, 20.502],
                                    [20.894, 20.286, 20.253],
                                    [21.228, 21.335, 21.061],
                                    [21.201, 21.002, 20.979],
                                    [21.266, 21.771, 21.111],
                                    [22.058, 22.077, 21.413],
                                    [21.537, 22.34, 21.619],
                                    [22.374, 22.441, 22.309],
                                    [22.522, 22.259, 22.563],
                                    [23.248, 22.452, 22.542],
                                    [22.768, 22.674, 23.169],
                                    [23.585, 23.053, 23.749],
                                    [23.649, 23.068, 23.016],
                                    [24.154, 23.828, 23.791],
                                    [24.146, 24.483, 23.912],
                                    [23.989, 23.954, 23.899],
                                    [24.663, 24.686, 24.552],
                                    [24.958, 24.981, 24.41],
                                    [24.847, 25.181, 24.871],
                                    [24.873, 25.657, 24.869]])
        )

        # data windows for test
        self.data_windows = {
            'close_E_d':     rolling_window(self.test_data['close_E_d'], 3),
            'close_E_h':     rolling_window(self.test_data['close_E_h'], 7),
            'close_E_5min':  rolling_window(self.test_data['close_E_5min'], 5),
            'close_E_15min': rolling_window(self.test_data['close_E_15min'], 8),
            'close_E_w':     rolling_window(self.test_data['close_E_w'], 6),
        }

        self.window_indices = {
            'close_E_d':     np.arange(15) + 5,
            'close_E_h':     np.arange(15),
            'close_E_5min':  np.arange(15) + 3,
            'close_E_15min': np.arange(15) + 1,
            'close_E_w':     np.arange(15) + 2,
        }

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
                         {'param1': (1, 100),
                          'param2': (0.0, 10.),
                          'param3': ('option1', 'option2', 'option3'),
                          'param4': (1.0, 5.0)})
        self.assertEqual(stg.par_types,
                         {'param1': 'int',
                          'param2': 'float',
                          'param3': 'enum',
                          'param4': 'float_array'})
        par_values = (50, 0.5, 'option1', np.array([1., 2., 3.]))
        stg.update_par_values(*par_values)
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
            'close_E_d':     'd',
            'close_E_h':     'h',
            'close_E_5min':  '5min',
            'close_E_15min': '15min',
            'close_E_w':     'w'
        })
        self.assertEqual(stg.data_ulc, {
            'close_E_d':     False,
            'close_E_h':     False,
            'close_E_5min':  False,
            'close_E_15min': False,
            'close_E_w':     False
        })
        self.assertEqual(stg.data_window_lengths, {
            'close_E_d':     3,
            'close_E_h':     7,
            'close_E_5min':  5,
            'close_E_15min': 8,
            'close_E_w':     6
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
        self.assertRaises(ValueError, stg.update_par_values, param2=11.5)  # out of range
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
        self.assertEqual(stg.par_range, {'param1': (1, 100), 'param2': (0.0, 10.)})
        self.assertEqual(stg.opt_tag, 1)
        self.assertEqual(stg.run_freq, '5min')
        self.assertEqual(stg.run_timing, 'open')
        self.assertEqual(stg.data_type_count, 3)
        self.assertEqual(stg.data_types, {'close_E_5min': self.dtype_3,
                                          'close_E_d':    self.dtype_1,
                                          'close_E_h':    self.dtype_2})
        self.assertEqual(stg.data_type_ids, ['close_E_5min', 'close_E_d', 'close_E_h'])
        self.assertEqual(stg.data_ids, ['close_E_5min', 'close_E_d', 'close_E_h'])
        self.assertEqual(stg.data_names, {'close_E_5min': 'close',
                                          'close_E_d':    'close',
                                          'close_E_h':    'close'})
        self.assertEqual(stg.data_freqs, {'close_E_5min': '5min',
                                          'close_E_d':    'd',
                                          'close_E_h':    'h'})
        self.assertEqual(stg.data_ulc, {'close_E_5min': False,
                                        'close_E_d':    False,
                                        'close_E_h':    False})
        self.assertEqual(stg.data_window_lengths, {'close_E_5min': 30,
                                                   'close_E_d':    30,
                                                   'close_E_h':    30})
        self.assertEqual(stg.window_lengths, {'close_E_5min': 30,
                                              'close_E_d':    30,
                                              'close_E_h':    30})
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
        self.assertEqual(stg.get_window_length('close_E_d'), 3)
        self.assertEqual(stg.get_window_length('close_E_h'), 7)
        self.assertEqual(stg.get_window_length('close_E_5min'), 5)
        self.assertEqual(stg.get_window_length('close_E_15min'), 8)
        self.assertEqual(stg.get_window_length('close_E_w'), 6)
        self.assertRaises(KeyError, stg.get_window_length, 'wrong_id')

        # test get_data_name method
        self.assertEqual(stg.get_data_name('close_E_d'), 'close')
        self.assertEqual(stg.get_data_name('close_E_h'), 'close')
        self.assertEqual(stg.get_data_name('close_E_5min'), 'close')
        self.assertEqual(stg.get_data_name('close_E_15min'), 'close')
        self.assertEqual(stg.get_data_name('close_E_w'), 'close')
        self.assertRaises(KeyError, stg.get_data_name, 'wrong_id')

        # test update_data_window method
        self.assertEqual(stg.share_count, 0)
        self.assertEqual(stg.share_names, [])

        stg.update_data_window(
                data_windows=self.data_windows,
                window_indices=self.window_indices,
                window_index=0
        )
        # check if the data windows are updated correctly
        print(f'after update_data_window:\n'
              f'close_E_d: \n{stg.close_E_d}\n'
              f'close_E_h: \n{stg.close_E_h}\n'
              f'close_E_5min: \n{stg.close_E_5min}\n'
              f'close_E_15min: \n{stg.close_E_15min}\n'
              f'close_E_w: \n{stg.close_E_w}\n')

        self.assertEqual(stg.share_count, 3)
        self.assertEqual(stg.share_names, [])

        stg.update_data_window(
                data_windows=self.data_windows,
                window_indices=self.window_indices,
                window_index=1
        )
        # check if the data windows are updated correctly
        print(f'after update_data_window:\n'
              f'close_E_d: \n{stg.close_E_d}\n'
              f'close_E_h: \n{stg.close_E_h}\n'
              f'close_E_5min: \n{stg.close_E_5min}\n'
              f'close_E_15min: \n{stg.close_E_15min}\n'
              f'close_E_w: \n{stg.close_E_w}\n')

    def test_general_strategy(self):
        """ 测试第一种基础策略类General Strategy"""
        stg = self.gen_stg
        stg.update_par_values(50, 0.5)

        # test info method
        stg.info()
        stg.info(verbose=True)

        # test creation of the object, and its properties
        self.assertIsInstance(stg, GeneralStg)
        self.assertEqual(stg.name, 'test_gen')
        self.assertEqual(stg.run_freq, 'd')
        self.assertEqual(stg.run_timing, 'close')
        self.assertEqual(stg.stg_type, 'GENERAL')
        self.assertEqual(stg.description, 'test general strategy')
        self.assertEqual(stg.par_values, (50, 0.5))
        self.assertEqual(stg.pars, {'param1': self.param1, 'param2': self.param2})
        self.assertEqual(stg.data_types, {'close_E_5min': self.dtype_3, 'close_E_d': self.dtype_1})

        # test if parameters are correct:
        self.assertEqual(stg.param1, 50)
        self.assertEqual(stg.param2, 0.5)
        self.assertEqual(stg.close_E_d, None)
        self.assertEqual(stg.close_E_5min, None)

        # update parameter and data windows before start generate()
        stg.update_par_values(3, 0.75)
        stg.update_data_window(
                data_windows=self.data_windows,
                window_indices=self.window_indices,
                window_index=0,  # run the first step of the indices
        )

        # check if parameters and data windows are set:
        self.assertEqual(stg.param1, 3)
        self.assertEqual(stg.param2, 0.75)
        self.assertIsInstance(stg.close_E_d, np.ndarray)
        self.assertIsInstance(stg.close_E_5min, np.ndarray)
        self.assertTrue(np.allclose(stg.close_E_d, self.data_windows['close_E_d'][5]))
        self.assertTrue(np.allclose(stg.close_E_5min, self.data_windows['close_E_5min'][3]))

        # run strategy.generate()
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)

        # update to the next data window:
        stg.update_data_window(
                data_windows=self.data_windows,
                window_indices=self.window_indices,
                window_index=1,  # run the first step of the indices
        )
        self.assertIsInstance(stg.close_E_d, np.ndarray)
        self.assertIsInstance(stg.close_E_5min, np.ndarray)
        self.assertTrue(np.allclose(stg.close_E_d, self.data_windows['close_E_d'][6]))
        self.assertTrue(np.allclose(stg.close_E_5min, self.data_windows['close_E_5min'][4]))

        print(f'running result in step 2: {stg.generate()}')

        for step in range(2, 10):
            stg.update_data_window(
                    data_windows=self.data_windows,
                    window_indices=self.window_indices,
                    window_index=step
            )
            self.assertTrue(np.allclose(stg.close_E_d, self.data_windows['close_E_d'][5 + step]))
            self.assertTrue(np.allclose(stg.close_E_5min, self.data_windows['close_E_5min'][3 + step]))

            print(f'running result in step {step}: {stg.generate()}')

        # test other aspects of the strategy, such as:
        # 1, modifying stg.data_ULC will impact the usage of data in each step （实际上不会有影响）

    def test_factor_sorter(self):
        """Test Factor Sorter 策略, test all built-in strategy parameters"""
        stg = self.factor_sorter_stg
        stg.update_par_values(10, 0.6)

        # test info method
        stg.info()
        stg.info(verbose=True)

        # test creation of the object, and its properties
        self.assertIsInstance(stg, FactorSorter)
        self.assertEqual(stg.name, 'test_factor_sorter')
        self.assertEqual(stg.run_freq, 'd')
        self.assertEqual(stg.run_timing, 'close')
        self.assertEqual(stg.stg_type, 'FACTOR')
        self.assertEqual(stg.description, 'test factor sorter strategy')
        self.assertEqual(stg.par_values, (10, 0.6))
        self.assertEqual(stg.pars, {'param1': self.param1, 'param2': self.param2})
        self.assertEqual(stg.data_types, {'close_E_5min': self.dtype_3, 'close_E_d': self.dtype_1})

        # test if parameters are correct:
        self.assertEqual(stg.param1, 10)
        self.assertEqual(stg.param2, 0.6)
        self.assertEqual(stg.close_E_d, None)
        self.assertEqual(stg.close_E_5min, None)

        # update parameter and data windows before start generate()
        stg.update_par_values(3, 0.75)
        stg.update_data_window(
                data_windows=self.data_windows,
                window_indices=self.window_indices,
                window_index=0,  # run the first step of the indices
        )

        # check if parameters and data windows are set:
        self.assertEqual(stg.param1, 3)
        self.assertEqual(stg.param2, 0.75)
        self.assertIsInstance(stg.close_E_d, np.ndarray)
        self.assertIsInstance(stg.close_E_5min, np.ndarray)
        self.assertTrue(np.allclose(stg.close_E_d, self.data_windows['close_E_d'][5]))
        self.assertTrue(np.allclose(stg.close_E_5min, self.data_windows['close_E_5min'][3]))

        self.assertEqual(stg.max_sel_count, 0.5)
        self.assertEqual(stg.condition, 'any')
        self.assertEqual(stg.lbound, -np.inf)
        self.assertEqual(stg.ubound, np.inf)
        self.assertEqual(stg.sort_ascending, False)
        self.assertEqual(stg.weighting, 'even')

        # run strategy.generate()
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 0, 1])))

        # text extra parameters of factor sorter such as max_sel_count,
        stg.max_sel_count = 0.7
        print('setting max_sel_count == 0.7')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 0.5, 0.5])))

        stg.weighting = 'ones'
        print('setting weighting == "ones"')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 1, 1])))

        stg.weighting = 'linear'
        print('setting weighting == "linear"')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 0.33333333, 0.66666667])))

        stg.weighting = 'distance'
        print('setting weighting == "distance"')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 0.08333333, 0.91666667])))

        stg.weighting = 'proportion'
        print('setting weighting == "proportion"')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 0.49470272, 0.50529728])))

        stg.weighting = 'wrong type'
        print('setting weighting == "distance"')
        self.assertRaises(KeyError, stg.generate)

        stg.sort_ascending = True
        stg.weighting = 'ones'
        print(f'setting sort_ascending = True')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([1, 1, 0])))

        stg.condition = 'greater'
        stg.ubound = 23.3
        print(f'setting condition = greater than 23.3')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 1, 1])))

        stg.condition = 'less'
        stg.lbound = 23.3
        stg.ubound = 23.3
        print(f'setting condition = less than 23.3')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([1, 0, 0])))

        stg.condition = 'between'
        stg.lbound = 23.3
        stg.ubound = 23.4
        print(f'setting condition = between 23.3 and 23.4')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 1, 0])))

        stg.condition = 'not_between'
        stg.lbound = 23.3
        stg.ubound = 23.4
        print(f'setting condition = not between 23.3 and 23.4')
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([1, 0, 1])))

        stg.condition = 'not_correct'
        self.assertRaises(ValueError, stg.generate)

    def test_rule_iterator(self):
        """测试rule_iterator类型策略"""
        stg = self.rule_iterator_stg
        stg.update_par_values(10, 0.6)

        # test info method
        stg.info()
        stg.info(verbose=True)

        # test creation of the object, and its properties
        self.assertIsInstance(stg, RuleIterator)
        self.assertEqual(stg.name, 'test_rule_iterator')
        self.assertEqual(stg.run_freq, 'd')
        self.assertEqual(stg.run_timing, 'close')
        self.assertEqual(stg.stg_type, 'RULE-ITER')
        self.assertEqual(stg.description, 'test rule iterator strategy')
        self.assertEqual(stg.par_values, (10, 0.6))
        self.assertEqual(stg.pars, {'param1': self.param1, 'param2': self.param2})
        self.assertEqual(stg.data_types, {'close_E_5min': self.dtype_3, 'close_E_d': self.dtype_1})

        # test if parameters are correct:
        self.assertEqual(stg.param1, 10)
        self.assertEqual(stg.param2, 0.6)
        self.assertEqual(stg.close_E_d, None)
        self.assertEqual(stg.close_E_5min, None)

        # update parameter and data windows before start generate()
        stg.update_par_values(5, 6)
        stg.update_data_window(
                data_windows=self.data_windows,
                window_indices=self.window_indices,
                window_index=0,  # run the first step of the indices
        )

        # check if parameters and data windows are set:
        self.assertEqual(stg.param1, 5)
        self.assertEqual(stg.param2, 6)
        self.assertIsInstance(stg._data_windows['close_E_d'], np.ndarray)
        self.assertIsInstance(stg._data_windows['close_E_5min'], np.ndarray)
        self.assertTrue(np.allclose(stg._data_windows['close_E_d'], self.data_windows['close_E_d'][5]))
        self.assertTrue(np.allclose(stg._data_windows['close_E_5min'], self.data_windows['close_E_5min'][3]))

        self.assertEqual(stg.allow_multi_par, True)
        self.assertEqual(stg.multi_pars, None)

        stg.allow_multi_par = False
        stg._update_multi_pars([(5, 5), (6, 1), (2, 4)])
        self.assertEqual(stg.allow_multi_par, False)
        self.assertEqual(stg.multi_pars, None)

        # run strategy.generate()
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([0, 0, 0])))

        # test run strategy with different stock parameters
        stg.allow_multi_par = True
        stg._update_multi_pars([(5, 5), (6, 1), (2, 4)])

        self.assertEqual(stg.param1, 5)
        self.assertEqual(stg.param2, 6)
        self.assertIsInstance(stg._data_windows['close_E_d'], np.ndarray)
        self.assertIsInstance(stg._data_windows['close_E_5min'], np.ndarray)
        self.assertTrue(np.allclose(stg._data_windows['close_E_d'], self.data_windows['close_E_d'][5]))
        self.assertTrue(np.allclose(stg._data_windows['close_E_5min'], self.data_windows['close_E_5min'][3]))

        self.assertEqual(stg.allow_multi_par, True)
        self.assertEqual(stg.multi_pars, ((5, 5), (6, 1), (2, 4)))

        # run strategy.generate()
        res = stg.generate()
        print(res)
        self.assertIsInstance(res, np.ndarray)
        self.assertTrue(np.allclose(res, np.array([1, 1, 0])))


if __name__ == '__main__':
    unittest.main()