# coding=utf-8
# ======================================
# File:     test_operator_and_strategy.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all Operator and
#   Strategy class attributes and
#   methods.
# ======================================
import unittest

from numba.cuda import runtime

import qteasy as qt
import pandas as pd
import numpy as np

from qteasy.parameter import Parameter
from qteasy.group import Group
from qteasy.built_in import SelectingAvgIndicator, DMA, MACD, CDL
from qteasy.tafuncs import sma
from qteasy.strategy import RuleIterator, GeneralStg, FactorSorter
from qteasy.datatypes import DataType
from qteasy.trading_util import _trade_time_index as tti

# test parameters and datatypes:
param1 = Parameter(
        name='param1',
        par_type='int',
        par_range=(1, 100),
        value=50,
)

param2 = Parameter(
        name='param2',
        par_type='float',
        par_range=(0.0, 10.),
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
        asset_type='E'
)

dtype_2 = DataType(
        name='close',
        freq='h',
        asset_type='E'
)

dtype_3 = DataType(
        name='close',
        freq='5min',
        asset_type='E'
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

# 测试数据的值不是来自于DataSource，而是直接设定，方便运算
dtype_1_data = np.array(
        [[0.994, 0.412, 0.876],
         [1.117, 1.257, 1.447],
         [2.315, 2.080, 2.799],
         [3.704, 3.870, 3.620],
         [6.091, 6.127, 6.218],
         [7.177, 7.337, 7.294],
         [8.240, 8.254, 8.626],
         [9.552, 9.446, 9.739],
         [10.754, 10.192, 10.650],
         [13.877, 13.685, 13.885],
         [14.556, 14.774, 14.250],
         [15.167, 15.026, 15.999],
         [16.580, 16.236, 16.307],
         [17.599, 17.797, 17.155],
         [27.921, 27.938, 27.481],
         [28.281, 28.604, 28.348],
         [29.062, 29.559, 29.880],
         [30.390, 30.247, 30.393],
         [31.902, 31.344, 31.878],
         [34.127, 34.099, 34.396],
         [35.332, 35.854, 35.131],
         [36.482, 36.229, 36.578],
         [37.435, 37.952, 37.289],
         [38.605, 38.377, 38.311],
         [41.676, 41.230, 41.839]],
)
dtype_2_data = np.array(
        [[0.296, 0.969, 0.422],
         [0.153, 0.306, 0.254],
         [0.793, 0.406, 0.798],
         [0.257, 0.461, 0.749],
         [1.201, 1.871, 1.381],
         [1.117, 1.665, 1.956],
         [1.040, 1.577, 1.919],
         [1.431, 1.490, 1.036],
         [2.634, 2.331, 2.445],
         [2.981, 2.116, 2.068],
         [2.646, 2.634, 2.910],
         [2.901, 2.668, 2.527],
         [3.217, 3.329, 3.680],
         [3.027, 3.806, 3.796],
         [3.047, 3.814, 3.564],
         [3.091, 3.168, 3.139],
         [6.273, 6.362, 6.544],
         [6.221, 6.621, 6.439],
         [6.990, 6.570, 6.894],
         [6.771, 6.277, 6.217],
         [7.140, 7.595, 7.823],
         [7.508, 7.924, 7.539],
         [7.065, 7.398, 7.163],
         [7.630, 7.433, 7.144],
         [8.988, 8.035, 8.454],
         [8.468, 8.776, 8.954],
         [8.057, 8.413, 8.022],
         [8.812, 8.767, 8.421],
         [9.974, 9.411, 9.576],
         [9.738, 9.484, 9.772],
         [9.390, 9.578, 9.635],
         [9.145, 9.801, 9.636],
         [10.093, 10.751, 10.501],
         [10.553, 10.952, 10.705],
         [10.803, 10.073, 10.546],
         [10.787, 10.033, 10.851],
         [13.340, 13.651, 13.768],
         [13.672, 13.798, 13.485],
         [13.715, 13.170, 13.580],
         [13.102, 13.216, 13.235],
         [14.304, 14.915, 14.385],
         [14.386, 14.645, 14.360],
         [14.569, 14.930, 14.235],
         [14.492, 14.152, 14.376],
         [15.367, 15.022, 15.234],
         [15.320, 15.186, 15.298],
         [15.252, 15.693, 15.582],
         [15.146, 15.020, 15.932],
         [16.687, 16.209, 16.238],
         [16.571, 16.912, 16.015],
         [16.118, 16.238, 16.120],
         [16.270, 16.909, 16.950],
         [17.636, 17.955, 17.647],
         [17.659, 17.512, 17.246],
         [17.531, 17.214, 17.680],
         [17.356, 17.611, 17.768],
         [27.391, 27.691, 27.099],
         [27.216, 27.734, 27.063],
         [27.534, 27.533, 27.873],
         [27.745, 27.081, 27.593]]
)
dtype_3_data = np.array(
        [[0.375, 0.370, 0.692],
         [0.983, 0.857, 0.961],
         [0.537, 0.462, 0.190],
         [0.510, 0.770, 0.116],
         [0.958, 0.129, 0.363],
         [0.778, 0.350, 0.849],
         [0.330, 0.420, 0.116],
         [0.246, 0.702, 0.462],
         [0.229, 0.207, 0.969],
         [0.941, 0.340, 0.615],
         [0.375, 0.014, 0.486],
         [0.110, 0.095, 0.324],
         [0.258, 0.809, 0.266],
         [0.425, 0.767, 0.464],
         [0.679, 0.314, 0.327],
         [0.390, 0.655, 0.378],
         [0.702, 0.377, 0.891],
         [0.855, 0.844, 0.990],
         [0.468, 0.934, 0.871],
         [0.051, 0.750, 0.554],
         [0.032, 0.958, 0.530],
         [0.807, 0.790, 0.116],
         [0.004, 0.479, 0.331],
         [0.395, 0.427, 0.779],
         [0.570, 0.193, 0.505],
         [0.900, 0.955, 0.863],
         [0.534, 0.036, 0.513],
         [0.516, 0.056, 0.359],
         [0.949, 0.903, 0.867],
         [0.027, 0.270, 0.913],
         [0.298, 0.337, 0.660],
         [0.677, 0.019, 0.780],
         [0.275, 0.345, 0.396],
         [0.061, 0.017, 0.924],
         [0.129, 0.398, 0.690],
         [0.289, 0.957, 0.184],
         [0.105, 0.755, 0.637],
         [0.388, 0.963, 0.431],
         [0.381, 0.378, 0.123],
         [0.520, 0.319, 0.818],
         [0.046, 0.050, 0.433],
         [0.646, 0.411, 0.850],
         [0.513, 0.281, 0.207],
         [0.344, 0.295, 0.425],
         [0.921, 0.263, 0.786],
         [0.077, 0.217, 0.871],
         [0.850, 0.649, 0.818],
         [0.885, 0.088, 0.525],
         [1.433, 1.209, 1.523],
         [1.013, 1.897, 1.519],
         [1.558, 1.484, 1.557],
         [1.005, 1.926, 1.709],
         [1.894, 1.196, 1.827],
         [1.354, 1.431, 1.649],
         [1.559, 1.759, 1.370],
         [1.077, 1.811, 1.832],
         [1.712, 1.541, 1.213],
         [1.506, 1.822, 1.654],
         [1.198, 1.949, 1.709],
         [1.222, 1.696, 1.856],
         [1.826, 1.224, 1.837],
         [1.087, 1.511, 1.413],
         [1.501, 1.391, 1.909],
         [1.384, 1.921, 1.849],
         [1.943, 1.121, 1.308],
         [1.983, 1.953, 1.041],
         [1.995, 1.570, 1.678],
         [1.781, 1.178, 1.794],
         [1.282, 1.602, 1.640],
         [1.718, 1.058, 1.298],
         [1.556, 1.472, 1.865],
         [1.686, 1.193, 1.469],
         [1.935, 1.317, 1.392],
         [1.067, 1.622, 1.936],
         [1.874, 1.187, 1.298],
         [1.294, 1.657, 1.086],
         [1.481, 1.221, 1.532],
         [1.322, 1.798, 1.976],
         [1.924, 1.553, 1.798],
         [1.564, 1.808, 1.729],
         [1.642, 1.099, 1.421],
         [1.895, 1.096, 1.931],
         [1.729, 1.487, 1.497],
         [1.325, 1.450, 1.282],
         [1.915, 1.491, 1.853],
         [1.142, 1.633, 1.685],
         [1.259, 1.669, 1.789],
         [1.002, 1.811, 1.781],
         [1.063, 1.718, 1.183],
         [1.384, 1.473, 1.794],
         [1.984, 1.189, 1.146],
         [1.197, 1.347, 1.499],
         [1.700, 1.894, 1.294],
         [1.146, 1.029, 1.737],
         [1.525, 1.055, 1.771],
         [1.165, 1.931, 1.213],
         [2.131, 2.803, 2.135],
         [2.632, 2.242, 2.884],
         [2.887, 2.505, 2.888],
         [2.514, 2.761, 2.412],
         [2.397, 2.106, 2.236],
         [2.038, 2.077, 2.195],
         [2.357, 2.516, 2.334],
         [2.833, 2.181, 2.605],
         [2.598, 2.510, 2.976],
         [2.296, 2.303, 2.914],
         [2.724, 2.226, 2.876],
         [2.146, 2.895, 2.770],
         [2.577, 2.967, 2.459],
         [2.258, 2.198, 2.924],
         [2.528, 2.151, 2.776],
         [2.901, 2.428, 2.869],
         [2.739, 2.544, 2.208],
         [2.754, 2.148, 2.708],
         [2.937, 2.628, 2.310],
         [2.464, 2.173, 2.258],
         [2.095, 2.613, 2.428],
         [2.079, 2.980, 2.146],
         [2.810, 2.864, 2.956],
         [2.629, 2.845, 2.401],
         [2.372, 2.331, 2.970],
         [2.571, 2.230, 2.877],
         [2.600, 2.421, 2.216],
         [2.749, 2.904, 2.195],
         [2.185, 2.628, 2.208],
         [2.935, 2.545, 2.074],
         [2.228, 2.898, 2.552],
         [2.306, 2.569, 2.771],
         [2.837, 2.099, 2.138],
         [2.434, 2.215, 2.945],
         [2.455, 2.709, 2.964],
         [2.573, 2.327, 2.824],
         [2.510, 2.889, 2.025],
         [2.158, 2.434, 2.110],
         [2.977, 2.127, 2.505],
         [2.959, 2.013, 2.220],
         [2.315, 2.814, 2.836],
         [2.791, 2.891, 2.459],
         [2.796, 2.187, 2.012],
         [2.347, 2.809, 2.569],
         [2.204, 2.624, 2.718],
         [2.644, 2.461, 2.504],
         [2.604, 2.019, 2.217],
         [2.050, 2.582, 2.758],
         [3.596, 3.793, 3.358],
         [3.681, 3.141, 3.088],
         [3.198, 3.032, 3.215],
         [3.768, 3.493, 3.155],
         [3.481, 3.702, 3.047],
         [3.224, 3.762, 3.572],
         [3.435, 3.432, 3.632],
         [3.168, 3.707, 3.589],
         [3.572, 3.775, 3.622],
         [3.692, 3.738, 3.133],
         [3.711, 3.733, 3.029],
         [3.621, 3.909, 3.529],
         [3.908, 3.253, 3.836],
         [3.071, 3.818, 3.627],
         [3.163, 3.677, 3.384],
         [3.686, 3.725, 3.747],
         [3.217, 3.133, 3.366],
         [3.659, 3.798, 3.597],
         [3.400, 3.885, 3.181],
         [3.840, 3.265, 3.905],
         [3.785, 3.116, 3.716],
         [3.429, 3.995, 3.700],
         [3.102, 3.577, 3.894],
         [3.859, 3.471, 3.924],
         [3.073, 3.426, 3.772],
         [3.484, 3.362, 3.732],
         [3.905, 3.197, 3.809],
         [3.782, 3.207, 3.759],
         [3.558, 3.547, 3.569],
         [3.956, 3.236, 3.780],
         [3.909, 3.511, 3.339],
         [3.787, 3.820, 3.105],
         [3.995, 3.039, 3.309],
         [3.580, 3.367, 3.577],
         [3.337, 3.210, 3.144],
         [3.802, 3.840, 3.544],
         [3.807, 3.947, 3.634],
         [3.478, 3.082, 3.435],
         [3.428, 3.279, 3.150],
         [3.183, 3.067, 3.299],
         [3.493, 3.589, 3.035],
         [3.815, 3.557, 3.462],
         [3.019, 3.028, 3.863],
         [3.223, 3.597, 3.738],
         [3.565, 3.076, 3.706],
         [3.309, 3.221, 3.165],
         [3.171, 3.399, 3.176],
         [3.235, 3.470, 3.381]]
)
dtype_4_data = np.array(
        [[6.496, 6.578, 6.001],
         [6.026, 6.351, 6.198],
         [6.678, 6.386, 6.985],
         [6.357, 6.467, 6.014],
         [6.319, 6.782, 6.705],
         [6.356, 6.091, 6.209],
         [6.122, 6.918, 6.729],
         [6.094, 6.073, 6.343],
         [6.611, 6.083, 6.345],
         [6.978, 6.881, 6.738],
         [6.206, 6.035, 6.697],
         [6.567, 6.524, 6.884],
         [6.966, 6.796, 6.849],
         [6.225, 6.695, 6.128],
         [6.540, 6.954, 6.556],
         [6.501, 6.598, 6.956],
         [7.311, 7.261, 7.459],
         [7.707, 7.215, 7.338],
         [7.019, 7.607, 7.370],
         [7.966, 7.234, 7.653],
         [7.786, 7.136, 7.881],
         [7.900, 7.981, 7.760],
         [7.670, 7.181, 7.087],
         [7.393, 7.691, 7.690],
         [7.105, 7.444, 7.785],
         [7.302, 7.523, 7.397],
         [7.087, 7.077, 7.015],
         [7.810, 7.072, 7.885],
         [7.220, 7.209, 7.478],
         [7.784, 7.135, 7.384],
         [7.811, 7.581, 7.935],
         [7.829, 7.697, 7.587],
         [8.008, 8.664, 8.347],
         [8.465, 8.989, 8.290],
         [8.799, 8.123, 8.340],
         [8.520, 8.206, 8.754],
         [8.249, 8.279, 8.512],
         [8.024, 8.334, 8.183],
         [8.356, 8.361, 8.163],
         [8.571, 8.723, 8.762],
         [8.852, 8.495, 8.681],
         [8.789, 8.230, 8.191],
         [8.882, 8.223, 8.282],
         [8.704, 8.756, 8.364],
         [8.296, 8.051, 8.166],
         [8.185, 8.655, 8.670],
         [8.517, 8.064, 8.100],
         [8.080, 8.098, 8.718],
         [9.572, 9.991, 9.070],
         [9.049, 9.279, 9.446],
         [9.992, 9.329, 9.424],
         [9.372, 9.480, 9.991],
         [9.234, 9.016, 9.956],
         [9.260, 9.751, 9.770],
         [9.377, 9.053, 9.150],
         [9.526, 9.540, 9.699],
         [9.800, 9.442, 9.388],
         [9.845, 9.364, 9.188],
         [9.011, 9.449, 9.809],
         [9.192, 9.383, 9.717],
         [9.455, 9.389, 9.182],
         [9.469, 9.272, 9.698],
         [9.887, 9.165, 9.732],
         [9.292, 9.677, 9.789],
         [10.506, 10.555, 10.518],
         [10.549, 10.890, 10.250],
         [10.107, 10.455, 10.229],
         [10.926, 10.772, 10.015],
         [10.617, 10.492, 10.495],
         [10.805, 10.823, 10.110],
         [10.204, 10.387, 10.865],
         [10.948, 10.027, 10.818],
         [10.015, 10.650, 10.124],
         [10.137, 10.699, 10.195],
         [10.662, 10.026, 10.602],
         [10.824, 10.391, 10.907],
         [10.004, 10.074, 10.118],
         [10.658, 10.596, 10.721],
         [10.160, 10.220, 10.649],
         [10.301, 10.176, 10.548],
         [13.948, 13.524, 13.069],
         [13.786, 13.199, 13.421],
         [13.806, 13.321, 13.119],
         [13.095, 13.178, 13.130],
         [13.637, 13.815, 13.054],
         [13.154, 13.894, 13.784],
         [13.724, 13.916, 13.176],
         [13.652, 13.150, 13.355],
         [13.209, 13.125, 13.323],
         [13.330, 13.619, 13.460],
         [13.680, 13.911, 13.869],
         [13.297, 13.313, 13.823],
         [13.002, 13.954, 13.198],
         [13.643, 13.256, 13.040],
         [13.477, 13.218, 13.066],
         [13.889, 13.438, 13.762],
         [14.174, 14.324, 14.294],
         [14.989, 14.918, 14.573],
         [14.944, 14.691, 14.977],
         [14.292, 14.964, 14.259],
         [14.709, 14.708, 14.709],
         [14.490, 14.309, 14.316],
         [14.103, 14.142, 14.989],
         [14.690, 14.319, 14.662],
         [14.443, 14.028, 14.810],
         [14.880, 14.006, 14.643],
         [14.032, 14.978, 14.125],
         [14.203, 14.874, 14.805],
         [14.727, 14.488, 14.435],
         [14.808, 14.819, 14.747],
         [14.582, 14.400, 14.771],
         [14.248, 14.325, 14.055],
         [15.125, 15.399, 15.519],
         [15.610, 15.894, 15.842],
         [15.054, 15.272, 15.731],
         [15.285, 15.986, 15.139],
         [15.824, 15.080, 15.709],
         [15.027, 15.595, 15.309],
         [15.301, 15.818, 15.289],
         [15.942, 15.990, 15.374],
         [15.101, 15.890, 15.207],
         [15.253, 15.705, 15.268],
         [15.217, 15.399, 15.725],
         [15.035, 15.070, 15.655],
         [15.047, 15.818, 15.061],
         [15.625, 15.998, 15.324],
         [15.120, 15.360, 15.089],
         [15.927, 15.127, 15.191],
         [16.637, 16.753, 16.807],
         [16.031, 16.856, 16.515],
         [16.091, 16.026, 16.302],
         [16.821, 16.327, 16.066],
         [16.700, 16.866, 16.226],
         [16.450, 16.249, 16.897],
         [16.456, 16.106, 16.598],
         [16.893, 16.122, 16.398],
         [16.131, 16.858, 16.872],
         [16.060, 16.793, 16.028],
         [16.744, 16.532, 16.339],
         [16.119, 16.862, 16.188],
         [16.844, 16.838, 16.060],
         [16.858, 16.167, 16.301],
         [16.222, 16.246, 16.499],
         [16.358, 16.863, 16.092],
         [17.683, 17.807, 17.261],
         [17.419, 17.759, 17.250],
         [17.398, 17.532, 17.773],
         [17.192, 17.250, 17.657],
         [17.243, 17.081, 17.615],
         [17.198, 17.900, 17.127],
         [17.539, 17.463, 17.219],
         [17.714, 17.199, 17.169],
         [17.109, 17.663, 17.129],
         [17.407, 17.546, 17.859],
         [17.011, 17.953, 17.526],
         [17.590, 17.502, 17.508],
         [17.819, 17.918, 17.637],
         [17.338, 17.277, 17.038],
         [17.579, 17.166, 17.275],
         [17.270, 17.029, 17.943],
         [27.477, 27.978, 27.552],
         [27.929, 27.826, 27.661],
         [27.314, 27.501, 27.455],
         [27.095, 27.426, 27.468],
         [27.089, 27.943, 27.504],
         [27.967, 27.234, 27.417],
         [27.412, 27.612, 27.110],
         [27.433, 27.657, 27.645],
         [27.476, 27.673, 27.100],
         [27.765, 27.185, 27.993],
         [27.613, 27.776, 27.817],
         [27.557, 27.492, 27.497],
         [27.750, 27.727, 27.281],
         [27.323, 27.904, 27.214],
         [27.117, 27.373, 27.823],
         [27.164, 27.599, 27.148]]
)
dtype_5_data = np.array(
        [[0.134, 0.207, 0.095],
         [1.015, 0.591, 0.615],
         [1.255, 0.850, 0.992]]
)

trade_price_h_data = np.array(
        [[37.58, 32.50, 24.14],
         [38.65, 33.31, 23.80],
         [38.50, 34.20, 24.52],
         [38.38, 34.10, 23.95],
         [38.80, 34.09, 26.35],
         [38.25, 34.12, 25.96],
         [38.92, 34.43, 25.14],
         [39.05, 34.12, 24.89],
         [39.66, 34.45, 25.78],
         [40.47, 35.48, 26.37],
         [40.68, 35.45, 25.99],
         [40.38, 35.21, 25.28],
         [40.65, 35.10, 24.91],
         [41.05, 35.05, 24.92],
         [42.03, 35.05, 25.30],
         [41.21, 34.63, 25.84],
         [40.54, 34.95, 26.08],
         [40.03, 34.88, 27.32],
         [39.30, 34.70, 27.18],
         [38.35, 33.84, 27.16],
         [38.41, 34.42, 27.16],
         [38.49, 34.29, 26.85],
         [38.49, 34.35, 28.50],
         [38.16, 34.27, 29.48],
         [37.72, 34.71, 28.93],
         [38.00, 34.87, 28.71],
         [37.17, 34.54, 29.28],
         [37.27, 34.15, 29.64],
         [36.71, 33.97, 29.23],
         [38.49, 35.15, 30.44],
         [38.69, 36.14, 29.67],
         [38.16, 36.08, 30.13],
         [38.27, 37.03, 29.54],
         [37.46, 36.56, 29.42],
         [37.16, 35.21, 29.02],
         [37.31, 35.52, 28.85],
         [38.25, 36.42, 29.18],
         [38.25, 36.61, 29.51],
         [38.25, 36.97, 28.69],
         [37.00, 36.91, 28.80]]
)

close_d_df = pd.DataFrame(
        dtype_1_data, columns=['A', 'B', 'C'],
        index=tti(start='2023-01-01', end='2023-02-13', freq='D') + pd.Timedelta(hours=15)  # len = 125
)
close_h_df = pd.DataFrame(
        dtype_2_data, columns=['A', 'B', 'C'], index=tti(start='2023-01-01', end='2023-01-31', freq='h',
                                                         include_start_pm=False, include_start_am=False)  # len = 60
)
close_5min_df = pd.DataFrame(
        dtype_3_data, columns=['A', 'B', 'C'], index=tti(start='2023-01-01', end='2023-01-08', freq='5min',
                                                         include_start_pm=False, include_start_am=False)  # len = 192
)
close_15min_df = pd.DataFrame(
        dtype_4_data, columns=['A', 'B', 'C'], index=tti(start='2023-01-07', end='2023-01-31', freq='15min',
                                                         include_start_pm=False, include_start_am=False)  # len = 176
)
close_w_df = pd.DataFrame(
        dtype_5_data, columns=['A', 'B', 'C'], index=tti(start='2023-01-01', end='2023-01-31', freq='w-fri')  # len = 3
)

trade_price_h_df = pd.DataFrame(
        trade_price_h_data, columns=['A', 'B', 'C'],
        index=tti(start='2023-01-10',
                  end='2023-01-31',
                  freq='h',
                  include_start_am=False,
                  include_start_pm=False)  # len = 40
)


# basic test strategies
class TestGenStg(GeneralStg):
    """用于Test测试的通用交易策略，基于GeneralStrategy策略生成

    策略没有参数，选股周期为5D
    在每个选股周期内，按以下逻辑选择股票并设定多空状态：
    当历史数据不含参考数据和交易结果数据时：
     - 计算：今日变化率 = (今收-昨收)/平均股价(HLC平均股价)，
     - 选择今日变化率最高的两支，设定投资比率50%，否则投资比例为0
    当给出参考数据时，按下面逻辑设定多空：
     - 计算：今日相对变化率 = (今收-昨收)/HLC平均股价/参考数据
     - 选择相对变化率最高的两只股票，设定投资比率为50%，否则为0
    当给出交易结果数据时，按下面逻辑设定多空：
     - 计算：交易价差变化率 = (今收-昨收)/上期交易价格
     - 选择交易价差变化率最高的两只股票，设定投资比率为50%，否则为0
    """

    def __init__(self, par_values: tuple = None, **kwargs):
        super().__init__(
                name='test_gen',
                description='test general strategy',
                pars=[param1, param2],
                data_types={'close_E_d': dtype_1, 'close_E_h': dtype_2},
                use_latest_data_cycle=[False, False],
                window_length=[4, 5],
                **kwargs,
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


class TestFactorSorter(FactorSorter):
    """用于Test测试的简单选股策略，基于Selecting策略生成

    策略没有参数，选股周期为5D
    在每个选股周期内，从股票池的三只股票中选出今日变化率 = (今收-昨收)/平均股价（OHLC平均股价）最高的两支，放入中选池，否则落选。
    选股比例为平均分配
    """

    def __init__(self, par_values=None, **kwargs):
        super().__init__(
                name='test_factor_sorter',
                description='test factor sorter strategy',
                pars=[param1, param2],
                data_types={'close_E_d': dtype_1, 'close_E_w': dtype_5},
                use_latest_data_cycle=[True, False],
                window_length=[3, 1],
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


class TestRuleIter(RuleIterator):
    """用于Test测试的简单信号生成策略，基于GeneralStrategy策略生成

    策略有三个参数，第一个参数为ratio，另外两个参数为price1以及price2
    ratio是k线形状比例的阈值，定义为abs((C-O)/(H-L))。当这个比值小于ratio阈值时，判断该K线为十字交叉（其实还有丁字等多种情形，但这里做了
    简化处理。
    如果历史数据中没有给出参考数据，也没有给出交易结果数据时，信号生成的规则如下：
     1，当某个K线出现十字交叉，且昨收与今收之差大于price1时，买入信号
     2，当某个K线出现十字交叉，且昨收与今收之差小于price2时，卖出信号
    如果给出参考数据(参考数据包含两个种类type1与type2)时，信号生成的规则如下：
     1，当某个K线出现十字交叉，且昨收与今收之差大于参考数据type1时，买入信号
     2，当某个K线出现十字交叉，且昨收与今收之差小于参考数据type2时，卖出信号
    如果给出交易结果数据时，信号生成的规则如下：
     1，当某个K线出现十字交叉，且昨收与今收之差大于上期交易价格时，买入信号
     2，当某个K线出现十字交叉，且昨收与今收之差小于上期交易价格时，卖出信号
    """

    def __init__(self, par_values=None, **kwargs):
        super().__init__(
                name='test_rule_iterator',
                description='test rule iterator strategy',
                pars=[param1, param2],
                data_types={'close_E_h': dtype_2, 'close_E_15min': dtype_4},
                use_latest_data_cycle=[True, False],
                window_length=[5, 20],
                **kwargs,
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


# Other high level test strategies
class MyStg(qt.RuleIterator):
    """自定义双均线择时策略策略"""

    def __init__(self, par_values=(20, 100, 0.01)):
        """这个均线择时策略只有三个参数：
            - SMA 慢速均线，所选择的股票
            - FMA 快速均线
            - M   边界值

            策略的其他说明

        """
        super().__init__(
                pars=[
                    Parameter((10, 250), par_type='int', name='f'),  # 快速均线
                    Parameter((10, 250), par_type='int', name='s'),  # 慢速均线
                    Parameter((0.0, 0.5), par_type='float', name='m'),  # 边界值
                ],
                name='CUSTOM ROLLING TIMING STRATEGY',
                description='Customized Rolling Timing Strategy for Testing',
                data_types=DataType('close'),
                window_length=200,
        )
        if par_values:
            self.update_par_values(*par_values)

    # 策略的具体实现代码写在策略的_realize()函数中
    # 这个函数固定接受两个参数： hist_price代表特定组合的历史数据， params代表具体的策略参数
    def realize(self):
        """策略的具体实现代码：
        s：短均线计算日期；l：长均线计算日期；m：均线边界宽度；hesitate：均线跨越类型"""
        f, s, m = self.f, self.s, self.m
        # 临时处理措施，在策略实现层对传入的数据切片，后续应该在策略实现层以外事先对数据切片，保证传入的数据符合data_types参数即可
        h = self.close_E_d  # 取最近200个交易日的数据进行计算
        # 计算长短均线的当前值
        s_ma = sma(h[0], s)[-1]
        f_ma = sma(h[0], f)[-1]

        # 计算慢均线的停止边界，当快均线在停止边界范围内时，平仓，不发出买卖信号
        s_ma_u = s_ma * (1 + m)
        s_ma_l = s_ma * (1 - m)
        # 根据观望模式在不同的点位产生Long/short/empty标记

        if f_ma > s_ma_u:  # 当快均线在慢均线停止范围以上时，持有多头头寸
            return 1
        elif s_ma_l <= f_ma <= s_ma_u:  # 当均线在停止边界以内时，平仓
            return 0
        else:  # f_ma < s_ma_l   当快均线在慢均线停止范围以下时，持有空头头寸
            return -1


class StgBuyOpen(GeneralStg):
    def __init__(self, par_values=(20,)):
        super().__init__(
                pars=[Parameter((0, 100), par_type='int', name='n')],
                name='OPEN_BUY',
                run_timing=DataType('open'),
                use_latest_data_cycle=False,
        )
        if par_values:
            self.update_par_values(*par_values)

    def realize(self):
        n, = self.n
        h = self.close_E_d
        current_price = h[:, -1, 0]
        n_day_price = h[:, -n, 0]
        # 选股指标为各个股票的N日涨幅
        factors = (current_price / n_day_price - 1).squeeze()
        # 初始化选股买卖信号，初始值为全0
        sig = np.zeros_like(factors)
        # buy_pos = np.nanargmax(factors)
        # sig[buy_pos] = 1
        # return sig
        if np.all(factors <= 0.002):
            # 如果所有的选股指标都小于0，则全部卖出
            # 但是卖出信号StgSelClose策略中处理，因此此处全部返回0即可
            return sig
        else:
            # 如果选股指标有大于0的，则找出最大者
            # 并生成买入信号
            sig[np.nanargmax(factors)] = 1
            return sig


class StgSelClose(GeneralStg):
    def __init__(self, par_values=(20,)):
        super().__init__(
                pars=[Parameter((0, 100), par_type='int', name='n')],
                name='SELL_CLOSE',
                run_timing=DataType('close'),
        )
        if par_values:
            self.update_par_values(*par_values)

    def realize(self):
        n, = self.n
        h = self.close_E_d
        current_price = h[:, -1, 0]
        n_day_price = h[:, -n, 0]
        # 选股指标为各个股票的N日涨幅
        factors = (current_price / n_day_price - 1).squeeze()
        # 初始化选股买卖信号，初始值为全-1
        sig = -np.ones_like(factors)
        # sig[np.nanargmax(factors)] = 0
        # return sig
        if np.all(factors <= 0.002):
            # 如果所有的选股指标都小于0，则全部卖出
            return sig
        else:
            # 如果选股指标有大于0的，则除最大者不卖出以外，其余全部
            # 产生卖出信号
            sig[np.nanargmax(factors)] = 0
            return sig


class TestOperatorAndStrategy(unittest.TestCase):
    """全面测试Operator对象的所有功能。包括：

        1, Strategy 参数的设置
        2, 历史数据的获取与分配提取
        3, 策略优化参数的批量设置和优化空间的获取
        4, 策略输出值的正确性验证
        5, 策略结果的混合结果确认
    """

    def setUp(self):
        """prepare arr for Operator test"""

        print('start testing HistoryPanel object\n')

        # 1， 准备模拟历史数据对象
        pass

    def test_init(self):
        """ test initialization of Operator class"""
        op = qt.Operator(name='test_operator')
        self.assertIsInstance(op, qt.Operator)
        self.assertIsInstance(op.strategies, list)
        self.assertEqual(len(op.strategies), 0)
        op = qt.Operator('dma')
        self.assertIsInstance(op, qt.Operator)
        self.assertIsInstance(op.strategies, list)
        self.assertIsInstance(op.strategies[0], DMA)
        op = qt.Operator('dma, macd')
        self.assertIsInstance(op, qt.Operator)
        op = qt.Operator(['dma', 'macd'])
        self.assertIsInstance(op, qt.Operator)

        # test init with other parameters like signal_type, run_freq, run_timing, group_merge_type
        op = qt.Operator('dma, macd', signal_type='ps')
        self.assertEqual(op.groups['Group_1'].signal_type, 'ps')

        op = qt.Operator('dma, macd', run_freq='15min')
        self.assertEqual(op.groups['Group_1'].run_freq, '15min')
        self.assertEqual(op['dma'].run_freq, '15min')
        self.assertEqual(op['macd'].run_freq, '15min')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertRaises(TypeError, qt.Operator, 'dma, macd', run_freq=15)
        self.assertRaises(ValueError, qt.Operator, 'dma, macd', run_freq='5hourly')

        op = qt.Operator('dma, macd', run_timing='open')
        self.assertEqual(op.groups['Group_1'].run_timing, 'open')
        self.assertEqual(op['dma'].run_timing, 'open')
        self.assertEqual(op['macd'].run_timing, 'open')
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')

        op = qt.Operator('dma, macd', group_merge_type='and')
        self.assertEqual(op.group_merge_type, 'and')
        self.assertRaises(TypeError, qt.Operator, 'dma, macd', group_merge_type=15)
        self.assertRaises(ValueError, qt.Operator, 'dma, macd', group_merge_type='wrong_type')

        op = qt.Operator('dma, macd', op_type='stepwise')
        self.assertEqual(op.op_type, 'stepwise')
        self.assertRaises(KeyError, qt.Operator, 'dma, macd', op_type=15)
        self.assertRaises(KeyError, qt.Operator, 'dma, macd', op_type='fast')

    def test_repr(self):
        """ test basic representation of Opeartor class"""
        op = qt.Operator()
        self.assertEqual(op.__repr__(), 'Operator([], \'batch\')')

        op = qt.Operator('macd, dma, trix, random, ndayavg')
        self.assertEqual(op.__repr__(), 'Operator([macd, dma, trix, random, ndayavg], \'batch\')')
        self.assertEqual(op['dma'].__repr__(), 'RULE-ITER(DMA, (12, 26, 9))')
        self.assertEqual(op['macd'].__repr__(), 'RULE-ITER(MACD, (None, None, None))')
        self.assertEqual(op['trix'].__repr__(), 'RULE-ITER(TRIX, (12, 12))')
        self.assertEqual(op['random'].__repr__(), 'GENERAL(RANDOM, (0.5,))')
        self.assertEqual(op['ndayavg'].__repr__(), 'FACTOR(N-DAY AVG, (14,))')

    def test_get_next_ids(self):
        """ test functions _next_stg_id and _next_group_id with fake ids"""
        op = qt.Operator()
        self.assertEqual(op.strategy_ids, [])

        # test getting next id in simple cases
        op.add_strategies('dma, macd, trix')
        self.assertEqual(op._next_stg_id('dma'), 'dma_1')
        self.assertEqual(op._next_stg_id('macd'), 'macd_1')
        self.assertEqual(op._next_stg_id('trix'), 'trix_1')
        self.assertEqual(op._next_stg_id('random'), 'random')

        # test getting next id in missing indexes
        op.add_strategies('dma, dma, dma')
        self.assertEqual(op._next_stg_id('dma'), 'dma_4')
        self.assertEqual(op._next_stg_id('macd'), 'macd_1')

        # test getting next group id in simple cases
        op = qt.Operator()
        self.assertEqual(op.group_ids, [])
        self.assertEqual(op._next_group_id(), 'Group_1')

        # test getting next group id in missing indexes
        op._groups = [Group('Group_1'),
                      Group('Group_3'),
                      Group('Group_5')]
        self.assertEqual(op._next_group_id(), 'Group_6')

    def test_operator_add_strategy(self):
        """test adding strategies to Operator"""
        op = qt.Operator('dma, all, sellrate')

        self.assertIsInstance(op, qt.Operator)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[1], qt.built_in.SelectingAll)
        self.assertIsInstance(op.strategies[2], qt.built_in.SellRate)
        self.assertIsInstance(op[0], qt.built_in.DMA)
        self.assertIsInstance(op[1], qt.built_in.SelectingAll)
        self.assertIsInstance(op[2], qt.built_in.SellRate)
        self.assertIsInstance(op['dma'], qt.built_in.DMA)
        self.assertIsInstance(op['all'], qt.built_in.SelectingAll)
        self.assertIsInstance(op['sellrate'], qt.built_in.SellRate)
        self.assertEqual(op.strategy_count, 3)
        self.assertEqual(op.strategy_ids, ['dma', 'all', 'sellrate'])
        print(f'test adding strategies into existing op')
        print('test adding strategy by string')
        op.add_strategy('macd')
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[3], qt.built_in.MACD)
        self.assertEqual(op.strategy_count, 4)
        op.add_strategy('random')
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[4], qt.built_in.SelectingRandom)
        self.assertEqual(op.strategy_count, 5)
        test_ls = TestGenStg()
        op.add_strategy(test_ls)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[5], TestGenStg)
        self.assertEqual(op.strategy_count, 6)
        print(f'Test different instance of objects are added to operator')
        op.add_strategy('dma')
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[6], qt.built_in.DMA)
        self.assertIsNot(op.strategies[0], op.strategies[6])
        print(f'Test adding strategy with class name')
        op.add_strategy(TestRuleIter)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[7], TestRuleIter)
        self.assertEqual(op.strategy_count, 8)
        self.assertEqual(op.strategy_ids,
                         ['dma', 'all', 'sellrate', 'macd', 'random', 'custom', 'dma_1', 'custom_1'])
        self.assertEqual(op.strategy_groups, {'Group_1': op._groups[0]})
        self.assertEqual(op.strategy_group_count, 1)

        print(f'create a new empty operator and add strategies with different run freq and run timing')
        op = qt.Operator()  # now operator has no strategy and no strategy group
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_group_count, 0)
        self.assertEqual(op.strategy_ids, [])
        self.assertEqual(op.group_ids, [])

        print(f'add a strategy with default run freq and run timing')
        op.add_strategy(TestRuleIter(run_freq='d', run_timing='close'))
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 1)
        self.assertEqual(op.strategy_group_count, 1)
        self.assertEqual(op.strategy_ids, ['custom'])
        self.assertEqual(op.group_ids, ['Group_1'])
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertTrue(all(stg.run_freq == 'd' for stg in op.groups['Group_1'].members))
        self.assertTrue(all(stg.run_timing == 'close' for stg in op.groups['Group_1'].members))

        print(f'add a strategy with run freq h and run timing close')
        op.add_strategy(TestRuleIter(run_freq='h', run_timing='close'))
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 2)
        self.assertEqual(op.strategy_group_count, 2)
        self.assertEqual(op.strategy_ids, ['custom', 'custom_1'])
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2'])
        self.assertEqual(op.groups['Group_2'].run_freq, 'h')
        self.assertEqual(op.groups['Group_2'].run_timing, 'close')
        self.assertTrue(all(stg.run_freq == 'h' for stg in op.groups['Group_2'].members))
        self.assertTrue(all(stg.run_timing == 'close' for stg in op.groups['Group_2'].members))

        print(f'add a strategy again with run freq d and run timing close')
        op.add_strategy(TestRuleIter(run_freq='d', run_timing='close'))
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 3)
        self.assertEqual(op.strategy_group_count, 2)
        self.assertEqual(op.strategy_ids, ['custom', 'custom_2', 'custom_1'])
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2'])
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertEqual(op.groups['Group_1'].strategy_count, 2)
        print(f'Group_1 has {op.groups["Group_1"].strategy_count} strategies')
        self.assertEqual(op.groups['Group_2'].strategy_count, 1)
        self.assertEqual(op.groups['Group_2'].run_freq, 'h')
        self.assertEqual(op.groups['Group_2'].run_timing, 'close')
        self.assertTrue(all(stg.run_freq == 'd' for stg in op.groups['Group_1'].members))
        self.assertTrue(all(stg.run_timing == 'close' for stg in op.groups['Group_1'].members))
        self.assertTrue(all(stg.run_freq == 'h' for stg in op.groups['Group_2'].members))
        self.assertTrue(all(stg.run_timing == 'close' for stg in op.groups['Group_2'].members))

        print(f'test adding strategy with run freq h and run timing open')
        op.add_strategy(TestRuleIter(run_freq='h', run_timing='open'))
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 4)
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.strategy_ids, ['custom', 'custom_2', 'custom_1', 'custom_3'])
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2', 'Group_3'])
        self.assertEqual(op.groups['Group_3'].run_freq, 'h')
        self.assertEqual(op.groups['Group_3'].run_timing, 'open')
        self.assertEqual(op.groups['Group_3'].strategy_count, 1)
        print(f'Group_3 has {op.groups["Group_3"].strategy_count} strategies')
        self.assertTrue(all(stg.run_freq == 'h' for stg in op.groups['Group_3'].members))
        self.assertTrue(all(stg.run_timing == 'open' for stg in op.groups['Group_3'].members))
        print(f'test adding strategy with run freq d and run timing close')
        op.add_strategy(TestRuleIter(run_freq='d', run_timing='close'))
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 5)
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.strategy_ids, ['custom', 'custom_2', 'custom_4', 'custom_1', 'custom_3'])
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2', 'Group_3'])
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertEqual(op.groups['Group_1'].strategy_count, 3)
        print(f'Group_1 has {op.groups["Group_1"].strategy_count} strategies')
        self.assertEqual(op.groups['Group_2'].strategy_count, 1)
        self.assertEqual(op.groups['Group_2'].run_freq, 'h')
        self.assertEqual(op.groups['Group_2'].run_timing, 'close')
        self.assertEqual(op.groups['Group_3'].strategy_count, 1)
        self.assertEqual(op.groups['Group_3'].run_freq, 'h')
        self.assertEqual(op.groups['Group_3'].run_timing, 'open')
        self.assertTrue(all(stg.run_freq == 'd' for stg in op.groups['Group_1'].members))
        self.assertTrue(all(stg.run_timing == 'close' for stg in op.groups['Group_1'].members))
        self.assertTrue(all(stg.run_freq == 'h' for stg in op.groups['Group_2'].members))
        self.assertTrue(all(stg.run_timing == 'close' for stg in op.groups['Group_2'].members))
        self.assertTrue(all(stg.run_freq == 'h' for stg in op.groups['Group_3'].members))
        self.assertTrue(all(stg.run_timing == 'open' for stg in op.groups['Group_3'].members))

    def test_operator_add_strategies(self):
        """ etst adding multiple strategies to Operator"""
        op = qt.Operator('dma, all, sellrate')
        self.assertEqual(op.strategy_count, 3)
        print('test adding multiple strategies -- adding strategy by list of strings')
        op.add_strategies(['dma', 'macd'])
        self.assertEqual(op.strategy_count, 5)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[3], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[4], qt.built_in.MACD)
        print('test adding multiple strategies -- adding strategy by comma separated strings')
        op.add_strategies('dma, macd')
        self.assertEqual(op.strategy_count, 7)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[5], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[6], qt.built_in.MACD)
        print('test adding multiple strategies -- adding strategy by list of strategies')
        op.add_strategies([qt.built_in.DMA(), qt.built_in.MACD()])
        self.assertEqual(op.strategy_count, 9)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[7], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[8], qt.built_in.MACD)
        print('test adding multiple strategies -- adding strategy by list of strategy and str')
        op.add_strategies(['DMA', qt.built_in.MACD()])
        self.assertEqual(op.strategy_count, 11)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[9], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[10], qt.built_in.MACD)
        self.assertIsNot(op.strategies[0], op.strategies[9])
        self.assertIs(type(op.strategies[0]), type(op.strategies[9]))
        print('test adding multiple strategies -- adding strategy by list of custom strategy and custom strategy names')
        op.add_strategies([TestGenStg, TestGenStg(), TestRuleIter()])
        self.assertEqual(op.strategy_count, 14)
        self.assertIsInstance(op.strategies[0], qt.built_in.DMA)
        self.assertIsInstance(op.strategies[11], TestGenStg)
        self.assertIsInstance(op.strategies[12], TestGenStg)
        self.assertIsInstance(op.strategies[13], TestRuleIter)
        self.assertIsNot(op.strategies[11], op.strategies[12])
        self.assertIsNot(op.strategies[11], op.strategies[13])
        self.assertIsNot(op.strategies[12], op.strategies[13])
        self.assertEqual(op.strategy_group_count, 1)
        self.assertEqual(op.groups, {'Group_1': op._groups[0]})
        print('test adding multiple strategies with different run freq and run timing')
        op.add_strategies([TestRuleIter(run_freq='d', run_timing='close'),
                           TestRuleIter(run_freq='h', run_timing='close'),
                           TestRuleIter(run_freq='h', run_timing='open')])
        self.assertEqual(op.strategy_count, 17)
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.strategy_ids, ['dma', 'all', 'sellrate', 'dma_1', 'macd', 'dma_2', 'macd_1',
                                           'custom', 'custom_1', 'dma_3', 'custom_2', 'custom_3', 'custom_4',
                                           'custom_5', 'custom_6', 'custom_7', 'custom_8'])
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2', 'Group_3'])
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertEqual(op.groups['Group_1'].strategy_count, 15)
        print(f'Group_1 has {op.groups["Group_1"].strategy_count} strategies')
        self.assertEqual(op.groups['Group_2'].run_freq, 'h')
        self.assertEqual(op.groups['Group_2'].run_timing, 'close')
        self.assertEqual(op.groups['Group_2'].strategy_count, 1)
        print(f'Group_2 has {op.groups["Group_2"].strategy_count} strategies')
        self.assertEqual(op.groups['Group_3'].run_freq, 'h')
        self.assertEqual(op.groups['Group_3'].run_timing, 'open')
        self.assertEqual(op.groups['Group_3'].strategy_count, 1)
        print(f'Group_3 has {op.groups["Group_3"].strategy_count} strategies')

        print(f'test adding multiple strategies with common run_timing and run_freq parameters')
        op.add_strategies([TestRuleIter, 'dma', TestGenStg], run_timing='open', run_freq='d')
        op.add_strategies(['macd', TestGenStg()], run_timing='close', run_freq='h')
        self.assertEqual(op.strategy_count, 22)
        self.assertEqual(op.strategy_group_count, 4)
        self.assertEqual(op.strategy_ids, [
            'dma', 'all', 'sellrate', 'dma_1', 'macd', 'dma_2',
            'macd_1', 'custom', 'custom_1', 'dma_3', 'custom_2',
            'custom_3', 'custom_4', 'custom_5', 'custom_6',
            'custom_7', 'macd_2', 'custom_11', 'custom_8',
            'custom_9', 'dma_4', 'custom_10'
        ])
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2', 'Group_3', 'Group_4'])
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertEqual(op.groups['Group_1'].strategy_count, 15)
        self.assertEqual(op.get_strategy_id_by_group('Group_1'), ['dma',
                                                                  'all',
                                                                  'sellrate',
                                                                  'dma_1',
                                                                  'macd',
                                                                  'dma_2',
                                                                  'macd_1',
                                                                  'custom',
                                                                  'custom_1',
                                                                  'dma_3',
                                                                  'custom_2',
                                                                  'custom_3',
                                                                  'custom_4',
                                                                  'custom_5',
                                                                  'custom_6'])
        self.assertEqual(op.get_strategy_count_by_group('Group_1'), 15)
        print(f'Group_1 has {op.groups["Group_1"].strategy_count} strategies')
        self.assertEqual(op.groups['Group_2'].run_freq, 'h')
        self.assertEqual(op.groups['Group_2'].run_timing, 'close')
        self.assertEqual(op.groups['Group_2'].strategy_count, 3)
        self.assertEqual(op.get_strategy_id_by_group('Group_2'), ['custom_7', 'macd_2', 'custom_11'])
        self.assertEqual(op.get_strategy_count_by_group('Group_2'), 3)
        print(f'Group_2 has {op.groups["Group_2"].strategy_count} strategies')
        self.assertEqual(op.groups['Group_3'].run_freq, 'h')
        self.assertEqual(op.groups['Group_3'].run_timing, 'open')
        self.assertEqual(op.groups['Group_3'].strategy_count, 1)
        self.assertEqual(op.get_strategy_id_by_group('Group_3'), ['custom_8'])
        self.assertEqual(op.get_strategy_count_by_group('Group_3'), 1)
        print(f'Group_3 has {op.groups["Group_3"].strategy_count} strategies')
        self.assertEqual(op.groups['Group_4'].run_freq, 'd')
        self.assertEqual(op.groups['Group_4'].run_timing, 'open')
        self.assertEqual(op.groups['Group_4'].strategy_count, 3)
        self.assertEqual(op.get_strategy_id_by_group('Group_4'), ['custom_9', 'dma_4', 'custom_10'])
        self.assertEqual(op.get_strategy_count_by_group('Group_4'), 3)
        print(f'Group_4 has {op.groups["Group_4"].strategy_count}')

        print('test adding fault arr')
        self.assertRaises(AssertionError, op.add_strategies, 123)
        self.assertRaises(AssertionError, op.add_strategies, None)

    def test_operator_remove_strategy(self):
        """ test method remove strategy"""

        print(f'create a new operator with 7 strategies in 3 groups')
        op = qt.Operator('dma, all, sellrate')
        op.add_strategies(['dma', 'macd'], run_freq='h', run_timing='close')
        op.add_strategies(['DMA', TestGenStg()], run_freq='h', run_timing='open')
        self.assertEqual(op.strategy_count, 7)
        self.assertEqual(op.strategy_ids, ['dma', 'all', 'sellrate', 'dma_1', 'macd', 'dma_2', 'custom'])
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.strategy_groups, {'Group_1': op._groups[0],
                                              'Group_2': op._groups[1],
                                              'Group_3': op._groups[2]}
                         )
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2', 'Group_3'])
        self.assertEqual(op.groups['Group_1'].strategy_count, 3)
        self.assertEqual(op.groups['Group_1'].members, [op['dma'], op['all'], op['sellrate']])
        self.assertEqual(op.groups['Group_2'].strategy_count, 2)
        self.assertEqual(op.groups['Group_2'].members, [op['dma_1'], op['macd']])
        self.assertEqual(op.groups['Group_3'].strategy_count, 2)
        self.assertEqual(op.groups['Group_3'].members, [op['dma_2'], op['custom']])
        print('test removing strategies from Operator')
        op.remove_strategy('dma')
        self.assertEqual(op.strategy_count, 6)
        self.assertEqual(op.strategy_ids, ['all', 'sellrate', 'dma_1', 'macd', 'dma_2', 'custom'])
        self.assertEqual(op.strategies[0], op['all'])
        self.assertEqual(op.strategies[1], op['sellrate'])
        self.assertEqual(op.strategies[2], op['dma_1'])
        self.assertEqual(op.strategies[3], op['macd'])
        self.assertEqual(op.strategies[4], op['dma_2'])
        self.assertEqual(op.strategies[5], op['custom'])
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.groups, {'Group_1': op._groups[0],
                                     'Group_2': op._groups[1],
                                     'Group_3': op._groups[2]})
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2', 'Group_3'])
        self.assertEqual(op.groups['Group_1'].strategy_count, 2)
        self.assertEqual(op.groups['Group_1'].members, [op['all'], op['sellrate']])
        self.assertEqual(op.groups['Group_2'].strategy_count, 2)
        self.assertEqual(op.groups['Group_2'].members, [op['dma_1'], op['macd']])
        self.assertEqual(op.groups['Group_3'].strategy_count, 2)
        self.assertEqual(op.groups['Group_3'].members, [op['dma_2'], op['custom']])

        print(f'testing remove both strategies from group2')
        op.remove_strategy('dma_1')
        op.remove_strategy('macd')
        self.assertEqual(op.strategy_count, 4)
        self.assertEqual(op.strategy_ids, ['all', 'sellrate', 'dma_2', 'custom'])
        self.assertEqual(op.strategies[0], op['all'])
        self.assertEqual(op.strategies[1], op['sellrate'])
        self.assertEqual(op.strategies[2], op['dma_2'])
        self.assertEqual(op.strategies[3], op['custom'])
        self.assertEqual(op.strategy_group_count, 2)
        self.assertEqual(op.groups, {'Group_1': op._groups[0],
                                     'Group_3': op._groups[1]})
        self.assertEqual(op.group_ids, ['Group_1', 'Group_3'])
        self.assertEqual(op.groups['Group_1'].strategy_count, 2)
        self.assertEqual(op.groups['Group_1'].members, [op['all'], op['sellrate']])
        self.assertEqual(op.groups['Group_3'].strategy_count, 2)
        self.assertEqual(op.groups['Group_3'].members, [op['dma_2'], op['custom']])

        print(f'testing add strategies back to operator originally in group2, now they should be in group4')
        op.add_strategies(['dma', 'macd'], run_freq='h', run_timing='close')
        self.assertEqual(op.strategy_count, 6)
        self.assertEqual(op.strategy_ids, ['all', 'sellrate', 'dma_2', 'custom', 'dma_3', 'macd'])
        self.assertEqual(op.strategies[0], op['all'])
        self.assertEqual(op.strategies[1], op['sellrate'])
        self.assertEqual(op.strategies[2], op['dma_2'])
        self.assertEqual(op.strategies[3], op['custom'])
        self.assertEqual(op.strategies[4], op['dma_3'])
        self.assertEqual(op.strategies[5], op['macd'])
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.groups, {'Group_1': op._groups[0],
                                     'Group_3': op._groups[1],
                                     'Group_4': op._groups[2]})
        self.assertEqual(op.group_ids, ['Group_1', 'Group_3', 'Group_4'])
        self.assertEqual(op.groups['Group_1'].strategy_count, 2)
        self.assertEqual(op.groups['Group_1'].members, [op['all'], op['sellrate']])
        self.assertEqual(op.groups['Group_3'].strategy_count, 2)
        self.assertEqual(op.groups['Group_3'].members, [op['dma_2'], op['custom']])
        self.assertEqual(op.groups['Group_4'].strategy_count, 2)
        self.assertEqual(op.groups['Group_4'].members, [op['dma_3'], op['macd']])

        # test removing strategy that does not exist
        print(f'test removing strategy that does not exist')
        self.assertRaises(ValueError, op.remove_strategy, 'not_exist')
        self.assertRaises(ValueError, op.remove_strategy, 'all_1')
        self.assertEqual(op.strategy_count, 6)
        self.assertEqual(op.strategy_ids, ['all', 'sellrate', 'dma_2', 'custom', 'dma_3', 'macd'])

        # test removing all strategies from operator
        print(f'test removing all strategies from operator')
        op.remove_strategy('all')
        op.remove_strategy('sellrate')
        op.remove_strategy('dma_2')
        op.remove_strategy('custom')
        op.remove_strategy('dma_3')
        op.remove_strategy('macd')
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])
        self.assertEqual(op.strategies, [])
        self.assertEqual(op.strategy_group_count, 0)
        self.assertEqual(op.group_ids, [])

    def test_operator_clear_strategies(self):
        """ test operator clear strategies"""
        op = qt.Operator('dma, all, sellrate')
        op.add_strategies(['dma', 'macd'], run_freq='h', run_timing='close')
        op.add_strategies(['DMA', TestGenStg()], run_freq='h', run_timing='open')
        self.assertEqual(op.strategy_count, 7)
        self.assertEqual(op.strategy_ids, ['dma', 'all', 'sellrate', 'dma_1', 'macd', 'dma_2', 'custom'])
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.strategy_groups, {'Group_1': op._groups[0],
                                              'Group_2': op._groups[1],
                                              'Group_3': op._groups[2]}
                         )
        print('test removing strategies from Operator')
        op.clear_strategies()
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])
        self.assertEqual(op.strategy_group_count, 0)
        self.assertEqual(op.strategy_groups, {})

        op.add_strategy('dma', par_values=(12, 123, 25), run_freq='5min', run_timing='open')
        self.assertEqual(op.strategy_count, 1)
        self.assertEqual(op.strategy_ids, ['dma'])
        self.assertEqual(type(op.strategies[0]), DMA)
        self.assertEqual(op.strategies[0].par_values, (12, 123, 25))
        self.assertEqual(op.strategy_group_count, 1)
        self.assertEqual(op.group_ids, ['Group_1'])
        self.assertEqual(op.groups, {'Group_1': op._groups[0]})
        self.assertEqual(op.groups['Group_1'].strategy_count, 1)
        self.assertEqual(op.groups['Group_1'].members, [op['dma']])
        self.assertEqual(op.groups['Group_1'].run_freq, '5min')
        self.assertEqual(op.groups['Group_1'].run_timing, 'open')

        op.clear_strategies()
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])
        self.assertEqual(op.strategy_group_count, 0)
        self.assertEqual(op.group_ids, [])

    def test_info(self):
        """Test information output of Operator"""
        op = qt.Operator('dma, macd, trix')
        stg = qt.built_in.SelectingNDayRateChange()  # factor sorter info
        print(f'\n  --==**  test printing information of strategies, in simple mode\n')
        op[0].info()
        print(f'\n  --==**  test printing information of strategies, in simple mode\n')
        stg.info()

        print(f'\n  --==**  test printing information of strategies, in verbose mode\n')
        op[0].info(verbose=True)
        print(f'\n  --==**  test printing information of strategies, in verbose mode\n')
        stg.info(verbose=True)

        print(f'\n  --==**  test printing information of operator object\n')
        op.info()

        op.add_strategies('dma, macd', run_freq='h', run_timing='close')
        op.add_strategies([TestRuleIter, TestGenStg, TestFactorSorter], run_freq='h', run_timing='open')
        print(f'\n  --==**  test printing information of operator in simple mode\n')

        op.info()
        print(f'\n  --==**  test printing information of operator in verbose mode\n')

        op.info(verbose=True)

    def test_set_par_values(self):
        """ 测试设置策略参数，使用update_par_values"""
        op = qt.Operator('dma, macd, trix')

        stg_dma = op[0]
        stg_macd = op[1]
        stg_trix = op[2]

        # test setting normal parameter values
        stg_dma.par_values = (10, 20, 30)
        self.assertEqual(stg_dma.par_values, (10, 20, 30))
        stg_macd.par_values = (10, 20, 30.)
        self.assertEqual(stg_macd.par_values, (10, 20, 30))
        stg_trix.update_par_values(10, 20)
        self.assertEqual(stg_trix.par_values, (10, 20))
        stg_dma.update_par_values(10, 20, 30)
        self.assertEqual(stg_dma.par_values, (10, 20, 30))
        # update par values with kwargs
        stg_macd.update_par_values(slow=10, fast=20, mid=30)
        self.assertEqual(stg_macd.par_values, (10, 20, 30))
        # update partial kwargs
        stg_macd.update_par_values(fast=25)
        self.assertEqual(stg_macd.par_values, (10, 25, 30))
        stg_macd.update_par_values(12, 13)
        self.assertEqual(stg_macd.par_values, (12, 13, 30))

        # test errors
        self.assertRaises(TypeError, stg_dma.update_par_values, 'wrong', 'input', 'type')  # wrong input type
        self.assertRaises(ValueError, stg_dma.update_par_values, 10, 10, 10, 10)  # par count does not match
        self.assertRaises(ValueError, stg_dma.update_par_values, 10, 10, -10)  # par out of range
        self.assertRaises(ValueError, stg_dma.update_par_values, 10, 10.5, -10)  # par type not match

        # test setting multi-parameters to RuleIterators
        op.add_strategy(TestRuleIter)

        stg_rule = op[3]
        self.assertIsInstance(stg_rule, TestRuleIter)
        self.assertEqual(stg_rule.par_values, (50, 0.5))
        stg_rule.update_par_values(20, 5)
        self.assertEqual(stg_rule.par_values, (20, 5))

        self.assertEqual(stg_rule.allow_multi_par, True)
        stg_rule.update_par_values(
                {'000001': (10, 3.),
                 '000002': (20, 5.),
                 '000003': (30, 7.)}
        )
        self.assertEqual(stg_rule.multi_pars, ((10, 3.0), (20, 5.0), (30, 7.0)))
        self.assertEqual(stg_rule.par_values, (10, 3.0))

        # update multi-parameter will fail if allow_multi_par is False
        stg_rule.allow_multi_par = False
        self.assertRaises(ValueError, stg_rule.update_par_values,
                          {'000001': (10, 10, 30),
                           '000002': (20, 20, 50),
                           '000003': (30, 30, 70)})

        # other types of strategies don't support multi-parameter
        op.add_strategy(GeneralStg)
        stg_gen = op[4]

        self.assertIsInstance(stg_gen, GeneralStg)
        self.assertEqual(stg_gen.par_values, ())
        self.assertRaises(ValueError, stg_gen.update_par_values,
                          {'000001': (10, 10, 30),
                           '000002': (20, 20, 50),
                           '000003': (30, 30, 70)})

    def test_get_strategy_by_id(self):
        """ test get_strategy_by_id()"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        self.assertEqual(op.strategy_ids, ['macd', 'dma', 'trix'])
        self.assertIs(op.get_strategy_by_id('macd'), op.strategies[0])
        self.assertIs(op.get_strategy_by_id(1), op.strategies[1])
        self.assertIs(op.get_strategy_by_id('trix'), op.strategies[2])

    def test_get_items(self):
        """ test method __getitem__(), it should be the same as geting strategies by stg_id"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op = qt.Operator('macd, dma, trix')
        self.assertEqual(op.strategy_ids, ['macd', 'dma', 'trix'])
        self.assertIs(op['macd'], op.strategies[0])
        self.assertIs(op['trix'], op.strategies[2])
        self.assertIs(op[1], op.strategies[1])
        self.assertIs(op[3], op.strategies[2])

    def test_get_strategies_by_group(self):
        """ test get_strategies_by_price_type"""
        op = qt.Operator()
        self.assertIsInstance(op, qt.Operator)
        self.assertEqual(op.strategy_count, 0)
        self.assertEqual(op.strategy_ids, [])

        op.add_strategies('dma, macd, trix', run_timing='open', run_freq='h')
        op.add_strategies('dma, macd, trix', run_timing='close', run_freq='h')
        op.add_strategies('dma, macd, trix', run_timing='close', run_freq='d')
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.group_names, ['Group_1', 'Group_2', 'Group_3'])
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2', 'Group_3'])
        self.assertEqual(op.strategy_groups, {'Group_1': op._groups[0],
                                              'Group_2': op._groups[1],
                                              'Group_3': op._groups[2]}
                         )

        stg_group1 = op.get_strategies_by_group('Group_1')
        stg_group2 = op.get_strategies_by_group('Group_2')
        stg_group3 = op.get_strategies_by_group('Group_3')

        self.assertIsInstance(stg_group1, list)
        self.assertIsInstance(stg_group2, list)
        self.assertIsInstance(stg_group3, list)

        self.assertEqual(stg_group1, [op['dma'], op['macd'], op['trix']])
        self.assertEqual(stg_group2, [op['dma_1'], op['macd_1'], op['trix_1']])
        self.assertEqual(stg_group3, [op['dma_2'], op['macd_2'], op['trix_2']])

        # test get strategies by passing wrong group name
        self.assertRaises(KeyError, op.get_strategies_by_group, 'not_exist')
        self.assertRaises(KeyError, op.get_strategies_by_group, 'Group_4')

        # test getting other strategy information by group
        self.assertEqual(op.get_strategy_count_by_group('Group_1'), 3)
        self.assertEqual(op.get_strategy_count_by_group('Group_2'), 3)
        self.assertEqual(op.get_strategy_count_by_group('Group_3'), 3)

        self.assertEqual(op.get_strategy_names_by_group('Group_1'), ['DMA', 'MACD', 'TRIX'])
        self.assertEqual(op.get_strategy_names_by_group('Group_2'), ['DMA', 'MACD', 'TRIX'])
        self.assertEqual(op.get_strategy_names_by_group('Group_3'), ['DMA', 'MACD', 'TRIX'])

        self.assertEqual(op.get_strategy_id_by_group('Group_1'), ['dma', 'macd', 'trix'])
        self.assertEqual(op.get_strategy_id_by_group('Group_2'), ['dma_1', 'macd_1', 'trix_1'])
        self.assertEqual(op.get_strategy_id_by_group('Group_3'), ['dma_2', 'macd_2', 'trix_2'])

    def test_property_strategies(self):
        """ test property strategies"""
        print(f'created a new simple Operator with only one strategy: DMA')
        op = qt.Operator('dma')
        strategies = op.strategies
        self.assertIsInstance(strategies, list)
        op.info()

        print(f'created the second simple Operator with three strategies')
        self.assertIsInstance(strategies[0], DMA)
        op = qt.Operator('dma, macd, cdl')
        strategies = op.strategies
        op.info()
        self.assertIsInstance(strategies, list)
        self.assertIsInstance(strategies[0], DMA)
        self.assertIsInstance(strategies[1], MACD)
        self.assertIsInstance(strategies[2], CDL)

    def test_group_properties(self):
        """ test property signal_type"""
        op = qt.Operator()
        op.add_strategies('dma, macd, trix')
        self.assertEqual(op.group_ids, ['Group_1'])
        group = op.groups['Group_1']
        self.assertIsInstance(group.signal_type, str)
        self.assertEqual(group.signal_type, 'pt')
        self.assertEqual(group.run_freq, 'd')
        self.assertEqual(group.run_timing, 'close')
        self.assertEqual(group.strategy_count, 3)
        self.assertEqual(group.members, [op['dma'], op['macd'], op['trix']])
        self.assertEqual(group.blender_str, '')
        self.assertEqual(group.human_blender, '')
        self.assertEqual(group.blender, None)

        op.groups['Group_1'].blender_str = 's0+s1+s2'
        self.assertEqual(group.blender_str, 's0+s1+s2')
        self.assertEqual(group.human_blender, 'DMA + MACD + TRIX')
        self.assertEqual(group.blender, ['+', 's2', '+', 's1', 's0'])

        op.add_strategies('dma, macd')
        self.assertEqual(group.strategy_count, 5)
        self.assertEqual(group.members, [op['dma'], op['macd'], op['trix'], op['dma_1'], op['macd_1']])
        self.assertEqual(group.blender_str, 's0+s1+s2')
        self.assertEqual(group.human_blender, 'DMA + MACD + TRIX')
        self.assertEqual(group.blender, ['+', 's2', '+', 's1', 's0'])

        group.blender_str = 's0*2+s3-s1+max(s1, s2)'
        self.assertEqual(group.blender_str, 's0*2+s3-s1+max(s1, s2)')
        self.assertEqual(group.human_blender, 'DMA * 2 + DMA - MACD + max(MACD, TRIX)')
        self.assertEqual(group.blender, ['+', 'max(2)', 's2', 's1', '-', 's1', '+', 's3', '*', '2', 's0'])

        op.add_strategies('dma', run_freq='h', run_timing='open')
        self.assertEqual(op.get_group_by_id('Group_1'), op.groups['Group_1'])
        self.assertEqual(op.get_group_by_id('Group_2'), op.groups['Group_2'])
        self.assertRaises(KeyError, op.get_group_by_id, 'not_exist')

    def test_property_op_data_types(self):
        """ test property op_data_types"""
        op = qt.Operator()
        self.assertIsInstance(op.op_data_types, list)
        self.assertEqual(op.op_data_types, [])

        op = qt.Operator('macd, dma, trix')
        dt = op.op_data_types
        self.assertEqual(dt[0], 'close_E_d')

        op = qt.Operator('macd, cdl')
        dt = op.op_data_types
        self.assertEqual(dt[0], 'close_E_d')
        self.assertEqual(dt[1], 'high_E_d')
        self.assertEqual(dt[2], 'low_E_d')
        self.assertEqual(dt[3], 'open_E_d')
        self.assertEqual(dt, ['close_E_d', 'high_E_d', 'low_E_d', 'open_E_d'])
        op.add_strategy('dma')
        dt = op.op_data_types
        self.assertEqual(dt[0], 'close_E_d')
        self.assertEqual(dt[1], 'high_E_d')
        self.assertEqual(dt[2], 'low_E_d')
        self.assertEqual(dt[3], 'open_E_d')
        self.assertEqual(dt, ['close_E_d', 'high_E_d', 'low_E_d', 'open_E_d'])

    def test_property_op_data_type_count(self):
        """ test property op_data_type_count"""
        op = qt.Operator()
        self.assertIsInstance(op.op_data_type_count, int)
        self.assertEqual(op.op_data_type_count, 0)

        op = qt.Operator('macd, dma, trix')
        dtn = op.op_data_type_count
        self.assertEqual(dtn, 1)
        op = qt.Operator('macd, cdl')
        dtn = op.op_data_type_count
        self.assertEqual(dtn, 4)
        op.add_strategy('dma')
        dtn = op.op_data_type_count
        self.assertEqual(dtn, 4)

    def test_property_op_data_freq(self):
        """ test property op_data_freq"""
        op = qt.Operator()
        self.assertIsInstance(op.op_data_freq, str)
        self.assertEqual(len(op.op_data_freq), 0)
        self.assertEqual(op.op_data_freq, '')

        op = qt.Operator('macd, dma, trix')
        dtf = op.op_data_freq
        self.assertIsInstance(dtf, str)
        self.assertEqual(dtf[0], 'd')
        op.set_parameter('macd', data_freq='m')

    def test_property_op_data_type_list(self):
        """ test property op_data_type_list"""
        op = qt.Operator()
        self.assertIsInstance(op.op_data_type_list, list)
        self.assertEqual(len(op.op_data_type_list), 0)
        self.assertEqual(op.op_data_type_list, [])

        op = qt.Operator('macd, dma, trix, cdl')
        ohd = op.op_data_type_list
        print(f'ohd is {ohd}')
        self.assertIsInstance(ohd, list)
        self.assertEqual(ohd[0], ['close'])
        op.set_parameter('macd', strategy_data_types='open, close')
        ohd = op.op_data_type_list
        print(f'ohd is {ohd}')
        self.assertIsInstance(ohd, list)
        self.assertEqual(len(ohd), 4)
        self.assertEqual(ohd[0], ['open', 'close'])
        self.assertEqual(ohd[1], ['close'])
        self.assertEqual(ohd[2], ['close'])
        self.assertEqual(ohd[3], ['open', 'high', 'low', 'close'])

    def test_property_opt_space_par(self):
        """ test property opt_space_par"""
        print(f'-----test property opt_space_par--------:\n')
        op = qt.Operator()
        self.assertIsInstance(op.opt_space_par, tuple)
        self.assertIsInstance(op.opt_space_par[0], list)
        self.assertIsInstance(op.opt_space_par[1], list)
        self.assertEqual(len(op.opt_space_par), 2)
        self.assertEqual(op.opt_space_par, ([], []))

        op = qt.Operator('macd, dma, trix, cdl')
        osp = op.opt_space_par
        print(f'before setting opt_tags opt_space_par is empty:\n'
              f'osp is {osp}\n')
        self.assertIsInstance(osp, tuple)
        self.assertEqual(osp[0], [])
        self.assertEqual(osp[1], [])
        op.set_parameter('macd', opt_tag=1)
        op.set_parameter('dma', opt_tag=1)
        osp = op.opt_space_par
        print(f'after setting opt_tags opt_space_par is not empty:\n'
              f'osp is {osp}\n')
        self.assertIsInstance(osp, tuple)
        self.assertEqual(len(osp), 2)
        self.assertIsInstance(osp[0], list)
        self.assertIsInstance(osp[1], list)
        self.assertEqual(len(osp[0]), 6)
        self.assertEqual(len(osp[1]), 6)
        self.assertEqual(osp[0], [(10, 250), (10, 250), (5, 250), (10, 250), (10, 250), (5, 250)])
        self.assertEqual(osp[1], ['int', 'int', 'int', 'int', 'int', 'int'])

    def test_property_opt_types(self):
        """ test property opt_tags"""
        print(f'-----test property opt_tags--------:\n')
        op = qt.Operator()
        self.assertIsInstance(op.opt_tags, list)
        self.assertEqual(len(op.opt_tags), 0)
        self.assertEqual(op.opt_tags, [])

        op = qt.Operator('macd, dma, trix, cdl')
        otp = op.opt_tags
        print(f'before setting opt_tags opt_space_par is empty:\n'
              f'otp is {otp}\n')
        self.assertIsInstance(otp, list)
        self.assertEqual(otp, [0, 0, 0, 0])
        op.set_parameter('macd', opt_tag=1)
        op.set_parameter('dma', opt_tag=1)
        otp = op.opt_tags
        print(f'after setting opt_tags opt_space_par is not empty:\n'
              f'otp is {otp}\n')
        self.assertIsInstance(otp, list)
        self.assertEqual(len(otp), 4)
        self.assertEqual(otp, [1, 1, 0, 0])

    def test_property_max_window_length(self):
        """ test property max_window_length"""
        print(f'-----test property max window length--------:\n')
        op = qt.Operator()
        self.assertIsInstance(op.max_window_length, int)
        self.assertEqual(op.max_window_length, 0)

        op = qt.Operator('macd, dma, trix, ndayvol')
        mwl = op.max_window_length
        print(f'before setting window_length the value is 270:\n'
              f'mwl is {mwl}\n')
        print(f'before setting window_length the max_window_length by dtype "close_E_d" is '
              f'{op.get_max_window_length_by_dtype("close_E_d")}:')
        print(f'before setting window_length the max_window_length by dtype "high_E_d" is '
              f'{op.get_max_window_length_by_dtype("high_E_d")}:')
        self.assertIsInstance(mwl, int)
        self.assertEqual(mwl, 270)
        self.assertEqual(op.get_max_window_length_by_dtype('close_E_d'), 270)
        self.assertEqual(op.get_max_window_length_by_dtype('high_E_d'), 150)

        op.set_parameter('macd', window_length=300)
        op.set_parameter('ndayvol', window_length=350)
        mwl = op.max_window_length
        print(f'after setting window_length the value is new set value:\n'
              f'mwl is {mwl}\n')
        print(f'after setting window_length the max_window_length by dtype "close_E_d" is '
              f'{op.get_max_window_length_by_dtype("close_E_d")}:')
        print(f'after setting window_length the max_window_length by dtype "high_E_d" is '
              f'{op.get_max_window_length_by_dtype("high_E_d")}:')
        self.assertIsInstance(mwl, int)
        self.assertEqual(mwl, 350)
        self.assertEqual(op.get_max_window_length_by_dtype('close_E_d'), 350)
        self.assertEqual(op.get_max_window_length_by_dtype('high_E_d'), 350)

        # update window_length with multiple values
        op.set_parameter('trix', window_length=(120,))
        op.set_parameter('macd', window_length=(90,))
        op.set_parameter('ndayvol', window_length=(90, 135, 45))

        print(f'set window_length again:')
        self.assertEqual(op['trix'].window_lengths, {'close_E_d': 120})
        self.assertEqual(op['macd'].window_lengths, {'close_E_d': 90})
        self.assertEqual(op['dma'].window_lengths, {'close_E_d': 30})
        self.assertEqual(op['ndayvol'].window_lengths, {'close_E_d': 45, 'high_E_d': 90, 'low_E_d': 135})
        self.assertEqual(op.max_window_length, 135)
        print(f'after setting window_length the max_window_length by dtype "close_E_d" is '
              f'{op.get_max_window_length_by_dtype("close_E_d")}:')
        print(f'after setting window_length the max_window_length by dtype "high_E_d" is '
              f'{op.get_max_window_length_by_dtype("high_E_d")}:')
        print(f'after setting window_length the max_window_length by dtype "low_E_d" is '
              f'{op.get_max_window_length_by_dtype("low_E_d")}:')

        self.assertEqual(op.get_max_window_length_by_dtype('close_E_d'), 120)
        self.assertEqual(op.get_max_window_length_by_dtype('high_E_d'), 90)
        self.assertEqual(op.get_max_window_length_by_dtype('low_E_d'), 135)

    def test_property_set(self):
        """ test all property setters:
            setting following properties:
            - strategy_blenders
            - signal_type
            other properties can not be set"""
        print(f'------- Test setting properties ---------')
        op_min = qt.Operator(strategies='DMA, MACD, ALL', run_freq='d', run_timing='open', signal_type='PS')
        op_min.set_blender(blender='(s0+s1)*s2')

        self.assertEqual(op_min.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op_min.groups['Group_1'].blender_str, '(s0+s1)*s2')
        self.assertEqual(op_min.groups['Group_1'].human_blender, '(DMA + MACD) * SIMPLE')
        self.assertEqual(op_min.groups['Group_1'].blender, ['*', 's2', '+', 's1', 's0'])

        op = qt.Operator('macd, dma, trix, cdl')
        # ckeck that op has only one group with all strategies
        self.assertEqual(op.strategy_group_count, 1)
        self.assertEqual(op.group_ids, ['Group_1'])
        self.assertEqual(op.strategy_groups, {'Group_1': op._groups[0]
                                              })
        self.assertEqual(op.get_strategy_id_by_group('Group_1'), ['macd', 'dma', 'trix', 'cdl'])
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertEqual(op.groups['Group_1'].signal_type, 'pt')
        self.assertEqual(op.groups['Group_1'].blender_str, '')
        self.assertEqual(op.groups['Group_1'].human_blender, '')
        self.assertEqual(op.groups['Group_1'].blender, None)

        # change run_freq and run_timing of some of the strategies, then groups will be changed
        op.set_parameter('dma', run_timing='open')
        op.set_parameter('cdl', run_freq='w')
        # check that op has two groups now
        self.assertEqual(op.strategy_group_count, 3)
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2', 'Group_3'])
        self.assertEqual(op.strategy_groups, {'Group_1': op._groups[0],
                                              'Group_2': op._groups[1],
                                              'Group_3': op._groups[2]}
                         )
        self.assertEqual(op.get_strategy_id_by_group('Group_1'), ['macd', 'trix'])
        self.assertEqual(op.get_strategy_id_by_group('Group_2'), ['dma'])
        self.assertEqual(op.get_strategy_id_by_group('Group_3'), ['cdl'])

        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertEqual(op.groups['Group_1'].signal_type, 'pt')
        self.assertEqual(op.groups['Group_1'].blender_str, '')
        self.assertEqual(op.groups['Group_1'].human_blender, '')
        self.assertEqual(op.groups['Group_1'].blender, None)
        self.assertEqual(op.groups['Group_2'].run_freq, 'd')
        self.assertEqual(op.groups['Group_2'].run_timing, 'open')
        self.assertEqual(op.groups['Group_2'].signal_type, 'pt')
        self.assertEqual(op.groups['Group_2'].blender_str, '')
        self.assertEqual(op.groups['Group_2'].human_blender, '')
        self.assertEqual(op.groups['Group_2'].blender, None)
        self.assertEqual(op.groups['Group_3'].run_freq, 'w')
        self.assertEqual(op.groups['Group_3'].run_timing, 'close')
        self.assertEqual(op.groups['Group_3'].signal_type, 'pt')
        self.assertEqual(op.groups['Group_3'].blender_str, '')
        self.assertEqual(op.groups['Group_3'].human_blender, '')
        self.assertEqual(op.groups['Group_3'].blender, None)

        # check all strategies are still in op.strategies
        self.assertEqual(op.strategy_count, 4)
        self.assertEqual(op.strategy_ids, ['macd', 'trix', 'dma', 'cdl'])

        # test setting group properties: run_timing, run_freq, signal_type, blender_str
        op.set_group_parameters('Group_1', signal_type='VS')
        self.assertEqual(op.groups['Group_1'].signal_type, 'vs')
        op.set_group_parameters('Group_1', blender_str='s0+s1')
        self.assertEqual(op.groups['Group_1'].blender_str, 's0+s1')
        self.assertEqual(op.groups['Group_1'].human_blender, 'MACD + TRIX')
        self.assertEqual(op.groups['Group_1'].blender, ['+', 's1', 's0'])

        op.set_group_parameters('Group_2', run_timing='close', run_freq='1min')
        # check that Group_2 properties are changed
        self.assertEqual(op.groups['Group_2'].run_timing, 'close')
        self.assertEqual(op.groups['Group_2'].run_freq, '1min')
        self.assertEqual(op.groups['Group_2'].signal_type, 'pt')
        self.assertEqual(op.groups['Group_2'].blender_str, '')
        # check that all strategies in group 2 has new run_timing and run_freq
        self.assertEqual(op['dma'].run_timing, 'close')
        self.assertEqual(op['dma'].run_freq, '1min')

        op.set_group_parameters('Group_3', run_timing='open', run_freq='30min', signal_type='PS', blender_str='s0')
        # check that Group_3 properties are changed
        self.assertEqual(op.groups['Group_3'].run_timing, 'open')
        self.assertEqual(op.groups['Group_3'].run_freq, '30min')
        self.assertEqual(op.groups['Group_3'].signal_type, 'ps')
        self.assertEqual(op.groups['Group_3'].blender_str, 's0')
        # check that all strategies in group 3 has new run_timing and run_freq
        self.assertEqual(op['cdl'].run_timing, 'open')
        self.assertEqual(op['cdl'].run_freq, '30min')

        # check that setting group3 the same run freq and run timing as group1 will merge the two groups
        op.set_group_parameters('Group_3', run_timing='close', run_freq='d')
        self.assertEqual(op.strategy_group_count, 2)
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2'])
        self.assertEqual(op.get_strategy_id_by_group('Group_1'), ['macd', 'trix', 'cdl'])
        self.assertEqual(op.get_strategy_id_by_group('Group_2'), ['dma'])
        self.assertEqual(op.groups['Group_1'].run_freq, 'd')
        self.assertEqual(op.groups['Group_1'].run_timing, 'close')
        self.assertEqual(op.groups['Group_1'].signal_type, 'vs')  #
        self.assertEqual(op.groups['Group_1'].blender_str, 's0+s1')  # blender info of group1 is lost after merging
        self.assertEqual(op.groups['Group_1'].human_blender, 'MACD + TRIX')
        self.assertEqual(op.groups['Group_2'].run_freq, '1min')
        self.assertEqual(op.groups['Group_2'].run_timing, 'close')
        self.assertEqual(op.groups['Group_2'].signal_type, 'pt')
        self.assertEqual(op.groups['Group_2'].blender_str, '')
        self.assertEqual(op.groups['Group_2'].human_blender, '')
        # check that group_3 no longer exists
        self.assertEqual(op.group_ids, ['Group_1', 'Group_2'])
        self.assertRaises(KeyError, op.get_group_by_id, 'Group_3')
        # check that all strategies are still in op.strategies
        self.assertEqual(op.strategy_count, 4)
        self.assertEqual(op.strategy_ids, ['macd', 'trix', 'cdl', 'dma'])

    def test_operator_ready(self):
        """test the method ready of Operator"""
        op = qt.Operator()
        print(f'operator is ready? "{op.ready}"')
        self.assertEqual(op.ready, False)
        print(f'checking why operator is not ready:\n')
        op.is_ready(
                tell_me_why=True,
        )

        print(f'Adding strategies to operator')
        op.add_strategies('dma, macd')
        print(f'operator is ready? "{op.ready}"')
        self.assertEqual(op.ready, False)
        print(f'checking why operator is not ready:\n')
        op.is_ready(
                tell_me_why=True,
        )

        print(f'Adding one more group of strategies and Setting up blenders for groups')
        op.add_strategies('trix, cdl', run_freq='h', run_timing='open')
        op.set_group_parameters('Group_1', blender_str='s0+s1')
        print(f'operator is ready? "{op.ready}"')
        self.assertEqual(op.ready, False)
        print(f'checking why operator is not ready:\n')
        op.is_ready(
                tell_me_why=True,
        )
        op.set_group_parameters('Group_2', blender_str='s0*s1')
        print(f'operator is ready? "{op.ready}"')
        self.assertEqual(op.ready, False)
        print(f'checking why operator is not ready:\n')
        op.is_ready(
                tell_me_why=True,
        )

        print(f'Adding historical data buffer to operator')
        # set stratety window lengths to be about 5 to 9
        op.set_parameter('dma', window_length=3)
        op.set_parameter('macd', window_length=6)
        op.set_parameter('trix', window_length=9)
        op.set_parameter('cdl', window_length=5)
        self.assertEqual(op.max_window_length, 9)
        all_dtypes = op.op_data_types
        data_buffer = {}
        for dtype in all_dtypes:
            data_buffer[dtype] = close_d_df
        start = close_d_df.index[10]
        end = close_d_df.index[-1]
        op.prepare_data_buffer(
                start_date=start,
                end_date=end,
                data_package=data_buffer,
        )
        print(f'operator is ready? "{op.ready}"')
        self.assertEqual(op.ready, False)
        print(f'checking why operator is not ready:\n')
        # import pdb; pdb.set_trace()
        op.is_ready(
                tell_me_why=True,
        )

        print(f'Preparing running schedule for operator')
        op.prepare_running_schedule(
                start_date=start,
                end_date=end,
        )
        print(f'operator is ready? "{op.ready}"')
        self.assertEqual(op.ready, False)
        print(f'checking why operator is not ready:\n')
        op.is_ready(
                tell_me_why=True,
        )

        print(f'Setting up data windows for strategies')
        op.create_data_windows()
        print(f'operator is ready? "{op.ready}"')
        self.assertEqual(op.ready, True)
        print(f'checking why operator is not ready:\n')
        op.is_ready(
                tell_me_why=True,
        )

    def test_operator_prepare_schedule(self):
        """测试Operator生成运行计划"""
        # test function prepare_running_schedule()

        op = qt.Operator()  # create an operator with many strategy groups with freq and timing diversity
        op.add_strategies('dma, macd')  # first group: d@close
        op.add_strategies('dma, macd', run_freq='h')  # second group: h@close
        op.add_strategies('dma, macd', run_freq='d', run_timing='open')  # third group: d@open
        op.add_strategies('dma, macd', run_freq='30min', run_timing='open')  # fourth group: 30min@open
        op.add_strategies('dma, macd', run_freq='d', run_timing='10:00')  # fifth group: d@10:00
        # op.add_strategies('dma, macd', run_freq='W-TUE', run_timing='11:00')  # TODO: sixth group: d@9:30
        # TODO: in the future, test group with run_freq like "W-TUE" or "M-5"(5th of month)

        op.prepare_running_schedule(
                start_date='2020-01-01',
                end_date='2020-01-04',
                trade_days_only=True,
        )
        print(f'operator running schedule is:\n')
        for group in op.groups:
            print(f'Group schedule for: "{group}:{op.groups[group]}"')
            print(op.group_schedules[group])

        # check details of the schedule of group 1
        schedule = op.group_schedules['Group_1']
        self.assertIsInstance(schedule, pd.DataFrame)
        self.assertEqual(len(schedule.index), 2)
        self.assertEqual(schedule.index[0], pd.Timestamp('2020-01-02 15:00:00'))
        self.assertEqual(schedule.index[-1], pd.Timestamp('2020-01-03 15:00:00'))

        # check details of the schedule of group 2
        schedule = op.group_schedules['Group_2']
        self.assertIsInstance(schedule, pd.DataFrame)
        self.assertEqual(len(schedule.index), 10)
        self.assertEqual(schedule.index[0], pd.Timestamp('2020-01-02 09:30:00'))
        self.assertEqual(schedule.index[1], pd.Timestamp('2020-01-02 10:30:00'))
        self.assertEqual(schedule.index[2], pd.Timestamp('2020-01-02 11:30:00'))
        self.assertEqual(schedule.index[3], pd.Timestamp('2020-01-02 14:00:00'))
        self.assertEqual(schedule.index[4], pd.Timestamp('2020-01-02 15:00:00'))
        self.assertEqual(schedule.index[9], pd.Timestamp('2020-01-03 15:00:00'))

        # check details of the schedule of group 3
        schedule = op.group_schedules['Group_3']
        self.assertIsInstance(schedule, pd.DataFrame)
        self.assertEqual(len(schedule.index), 2)
        self.assertEqual(schedule.index[0], pd.Timestamp('2020-01-02 09:30:00'))
        self.assertEqual(schedule.index[-1], pd.Timestamp('2020-01-03 09:30:00'))

        # check details of the schedule of group 4
        schedule = op.group_schedules['Group_4']
        self.assertIsInstance(schedule, pd.DataFrame)
        self.assertEqual(len(schedule.index), 18)
        self.assertEqual(schedule.index[0], pd.Timestamp('2020-01-02 09:30:00'))
        self.assertEqual(schedule.index[1], pd.Timestamp('2020-01-02 10:00:00'))
        self.assertEqual(schedule.index[2], pd.Timestamp('2020-01-02 10:30:00'))
        self.assertEqual(schedule.index[3], pd.Timestamp('2020-01-02 11:00:00'))
        self.assertEqual(schedule.index[4], pd.Timestamp('2020-01-02 11:30:00'))
        self.assertEqual(schedule.index[5], pd.Timestamp('2020-01-02 13:30:00'))
        self.assertEqual(schedule.index[6], pd.Timestamp('2020-01-02 14:00:00'))
        self.assertEqual(schedule.index[7], pd.Timestamp('2020-01-02 14:30:00'))
        self.assertEqual(schedule.index[8], pd.Timestamp('2020-01-02 15:00:00'))
        self.assertEqual(schedule.index[9], pd.Timestamp('2020-01-03 09:30:00'))
        self.assertEqual(schedule.index[10], pd.Timestamp('2020-01-03 10:00:00'))
        self.assertEqual(schedule.index[11], pd.Timestamp('2020-01-03 10:30:00'))
        self.assertEqual(schedule.index[12], pd.Timestamp('2020-01-03 11:00:00'))
        self.assertEqual(schedule.index[13], pd.Timestamp('2020-01-03 11:30:00'))
        self.assertEqual(schedule.index[14], pd.Timestamp('2020-01-03 13:30:00'))
        self.assertEqual(schedule.index[15], pd.Timestamp('2020-01-03 14:00:00'))
        self.assertEqual(schedule.index[16], pd.Timestamp('2020-01-03 14:30:00'))
        self.assertEqual(schedule.index[17], pd.Timestamp('2020-01-03 15:00:00'))
        self.assertEqual(schedule.index[-1], pd.Timestamp('2020-01-03 15:00:00'))

        # check details of the schedule of group 5
        schedule = op.group_schedules['Group_5']
        self.assertIsInstance(schedule, pd.DataFrame)
        self.assertEqual(len(schedule.index), 2)
        self.assertEqual(schedule.index[0], pd.Timestamp('2020-01-02 10:00:00'))
        self.assertEqual(schedule.index[-1], pd.Timestamp('2020-01-03 10:00:00'))

    def test_operator_assign_history_data(self):
        """测试分配Operator运行所需历史数据"""
        # create an operator with 2 groups of strategies
        op = qt.Operator()
        op.add_strategies([TestGenStg, TestFactorSorter])  # first group: d@close
        op.add_strategies([TestRuleIter], run_freq='h')  # second group: h@close
        print(f'Operator created with {op.strategy_group_count} groups of strategies:\n')
        op.info(verbose=False)

        op.prepare_running_schedule(
                start_date='2023-01-10',
                end_date='2023-01-31',
                include_start_am=False,
                include_start_pm=False,
        )
        print(f'Operator running schedule prepared:\n')
        for group in op.groups:
            print(f'Group schedule for: "{group}:{op.groups[group]}"')
            print(op.group_schedules[group])
            self.assertIsInstance(op.group_schedules[group], pd.DataFrame)
        group = 'Group_1'
        self.assertEqual(len(op.group_schedules[group].index), 10)
        self.assertEqual(op.group_schedules[group].index[0], pd.Timestamp('2023-01-10 15:00:00'))
        self.assertEqual(op.group_schedules[group].index[-1], pd.Timestamp('2023-01-30 15:00:00'))
        group = 'Group_2'
        self.assertEqual(len(op.group_schedules[group].index), 40)
        self.assertEqual(op.group_schedules[group].index[0], pd.Timestamp('2023-01-10 10:30:00'))
        self.assertEqual(op.group_schedules[group].index[-1], pd.Timestamp('2023-01-30 15:00:00'))

        # test function prepare_data_buffer()

        print(f'Preparing data buffer for operator')
        print(f'Operator data types needed are: {op.op_data_types}')
        data_buffer = {
            'close_E_15min': close_15min_df,
            'close_E_d': close_d_df,
            'close_E_h': close_h_df,
            'close_E_w': close_w_df,
        }
        op.prepare_data_buffer(
                start_date='2023-01-11',
                end_date='2023-01-31',
                data_package=data_buffer,
        )
        print(f'Operator data buffer prepared:\n')
        for dtype in op.op_data_types:
            print(f'Data type "{dtype}" has data:\n')
            print(op.data_buffers[dtype])
            print('\n')

        print(f'Data Windows are NOT created for all strategies')
        self.assertEqual(op.data_window_views, {})
        self.assertEqual(op.data_window_indices, {})

        # test function create_data_windows()
        op.create_data_windows()
        print(f'Data Windows created for all strategies')
        self.assertEqual(len(op.data_window_views), 3)
        self.assertEqual(len(op.data_window_indices), 3)
        # import pdb; pdb.set_trace()
        for stg_id in op.strategy_ids:
            print(f'Strategy "{stg_id}" has data window for its data types:\n'
                  f'{op[stg_id].data_types}\n')
            for dtype in op[stg_id].data_types:
                print(f'Data type "{dtype}" has data window:\n'
                      f'{op.data_window_views[stg_id][dtype][:3]}\n'
                      f'with window indices: {op.data_window_indices[stg_id][dtype]}\n'
                      )
                # check data type and data shapes
                self.assertIn(dtype, op.op_data_types)
                self.assertIsInstance(op.data_window_views[stg_id][dtype], np.ndarray)
                self.assertIsInstance(op.data_window_indices[stg_id][dtype], np.ndarray)
                self.assertEqual(op.data_window_views[stg_id][dtype].shape[1],
                                 op[stg_id].window_lengths[dtype])
                # import pdb; pdb.set_trace()
                self.assertEqual(op.data_window_views[stg_id][dtype].shape[2],
                                 3)

        raise NotImplementedError

    def test_set_opt_par(self):
        """ test setting opt pars in batch"""
        print(f'--------- Testing setting Opt Pars: set_opt_par -------')
        op = qt.Operator('dma, random, crossline')
        op.set_parameter('dma',
                         opt_tag=1,
                         window_length=10, )
        op.set_parameter('dma',
                         par_values=(50, 10, 55))
        self.assertEqual(op.strategies[0].par_values, (50, 10, 55))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (35, 120, 0.02))
        self.assertEqual(op.opt_tags, [1, 0, 0])
        op.set_opt_par((58, 12, 90))
        self.assertEqual(op.strategies[0].par_values, (58, 12, 90))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (35, 120, 0.02))

        op.set_parameter('crossline',
                         opt_tag=1,
                         window_length=10, )
        op.set_parameter('crossline',
                         par_values=(55, 10, 0.1))
        self.assertEqual(op.opt_tags, [1, 0, 1])
        op.set_opt_par((60, 12, 99, 80, 26, 0.09))
        self.assertEqual(op.strategies[0].par_values, (60, 12, 99))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (80, 26, 0.09))

        op.set_opt_par((90, 200, 155, 80, 26, 0.09, 5, 12, 9))
        self.assertEqual(op.strategies[0].par_values, (90, 200, 155))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (80, 26, 0.09))

        # test set_opt_par when opt_tag is set to be 2 (enumerate type of parameters)
        op.set_parameter('crossline',
                         opt_tag=2,
                         window_length=10, )
        op.set_parameter('crossline',
                         par_values=(50, 10, 0.05))
        self.assertEqual(op.opt_tags, [1, 0, 2])
        self.assertEqual(op.strategies[0].par_values, (90, 200, 155))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (50, 10, 0.05))
        op.set_opt_par((15, 12, 9, (18, 26, 0.09)))
        self.assertEqual(op.strategies[0].par_values, (15, 12, 9))
        self.assertEqual(op.strategies[1].par_values, (0.5,))
        self.assertEqual(op.strategies[2].par_values, (18, 26, 0.09))

        # Test Errors
        # op.set_opt_par主要在优化过程中自动生成，已经保证了参数的正确性，因此不再检查参数正确性

    def test_operator_generate(self):
        """ 测试operator对象生成完整交易信号

        :return:
        """
        raise NotImplementedError

    def test_operator_generate_stepwise(self):
        """ 测试operator对象在实时模式下生成交易信号
        """
        # TODO: implement this test
        raise NotImplementedError

    def test_stg_trading_different_prices(self):
        """测试一个以开盘价买入，以收盘价卖出的大小盘轮动交易策略"""
        # 测试大小盘轮动交易策略，比较两个指数的过去N日收盘价涨幅，选择较大的持有，以开盘价买入，以收盘价卖出
        print('\n测试大小盘轮动交易策略，比较两个指数的过去N日收盘价涨幅，选择较大的持有，以开盘价买入，以收盘价卖出')
        stg_buy = StgBuyOpen()
        stg_sel = StgSelClose()
        op = qt.Operator(strategies=[stg_buy, stg_sel], signal_type='ps')
        op.set_parameter(
                0,
                data_freq='d',
                run_freq='d',
                window_length=50,
                pars=(20,),
                strategy_data_types='close',  # 考察收盘价变化率
                run_timing='open',  # 以开盘价买进(这个策略只处理买入信号)
        )
        op.set_parameter(
                1,
                data_freq='d',
                run_freq='d',
                window_length=50,
                pars=(20,),
                strategy_data_types='close',  # 考察收盘价的变化率
                run_timing='close',  # 以收盘价卖出(这个策略只处理卖出信号)
        )
        op.set_blender(blender='s0')
        op.get_blender()
        qt.configure(asset_pool=['000300.SH',
                                 '399006.SZ'],
                     asset_type='IDX')
        res = qt.run(op,
                     mode=1,
                     visual=True,
                     trade_log=True,
                     invest_start='20110725',
                     invest_end='20220401',
                     trade_batch_size=1,
                     sell_batch_size=0)
        stock_pool = qt.filter_stock_codes(index='000300.SH', date='20211001')
        qt.configure(asset_pool=stock_pool,
                     asset_type='E',
                     benchmark_asset='000300.SH',
                     benchmark_asset_type='IDX',
                     opti_output_count=50,
                     invest_start='20211013',
                     invest_end='20211231',
                     opti_sample_count=100,
                     trade_batch_size=100.,
                     sell_batch_size=100.,
                     invest_cash_amounts=[1000000],
                     mode=1,
                     trade_log=True,
                     PT_buy_threshold=0.03,
                     PT_sell_threshold=0.03,
                     backtest_price_adj='none')

    def test_stg_index_follow(self):
        # 跟踪沪深300指数的价格，买入沪深300指数成分股并持有，计算收益率
        print('\n跟踪沪深300指数的价格，买入沪深300指数成分股并持有，计算收益率')
        op = qt.Operator(strategies=['finance'], signal_type='PS')
        op.set_parameter(0,
                         opt_tag=1,
                         run_freq='M',
                         strategy_data_types='wt_idx|000300.SH',
                         sort_ascending=False,
                         weighting='proportion',
                         max_sel_count=300)
        res = qt.run(op,
                     mode=1,
                     visual=True,
                     trade_log=True)

    def test_non_day_data_freqs(self):
        """测试除d之外的其他数据频率交易策略"""
        raise NotImplementedError

    def test_long_short_position_limits(self):
        """ 测试多头和空头仓位的最高仓位限制 """
        # TODO: implement this test
        pass


if __name__ == '__main__':
    unittest.main()