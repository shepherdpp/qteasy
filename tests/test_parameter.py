# coding=utf-8
# ======================================
# File:     test_parameter.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-08-12
# Desc:
#   Unittest for all functionalities of
# Parameter class, including blending
# functions.
# ======================================

import unittest
import numpy as np
import math

from qteasy.parameter import Parameter
from qteasy.blender import (
    blender_parser,
    signal_blend,
    human_blender,
    _exp_to_token,
)


class TestParameter(unittest.TestCase):
    def test_parameter(self):
        p = Parameter((0, 10),name='par1')
        self.assertEqual(p.name, 'par1')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.par_range, (0, 10))
        self.assertEqual(p.count, 11)
        self.assertEqual(p.size, 11)
        self.assertEqual(p.shape, None)
        self.assertEqual(p.dim, 0)
        self.assertEqual(p.array_size, 1)
        self.assertEqual(p.upper_bound, 10)
        self.assertEqual(p.lower_bound, 0)
        self.assertEqual(p.value, None)
        self.assertTrue(np.allclose(p.gen_values(11, 'int'), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
        self.assertRaises(ValueError, p.gen_values, 0.5, 'int')
        extracted = p.gen_values(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(0 <= item <= 10) for item in extracted]))
        self.assertTrue(all([item in p for item in extracted]))
        self.assertIsNone(p.value)
        p.set_value(7)
        self.assertEqual(p.value, 7)
        p.value=8
        self.assertEqual(p.value, 8)
        self.assertEqual(list(p.enum_values()), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.assertEqual(str(p), "Parameter((0, 10), 'int')")

        self.assertRaises(TypeError, p.set_value, 'wrong_type')
        self.assertRaises(ValueError, p.set_value, 7.5)
        self.assertRaises(ValueError, p.set_value, 11)

        p = Parameter((0.0, 1.0), name='par2')
        self.assertEqual(p.name, 'par2')
        self.assertEqual(p.par_type, 'float')
        self.assertEqual(p.par_range, (0.0, 1.0))
        self.assertEqual(p.count, np.inf)
        self.assertEqual(p.size, 1.0)
        self.assertEqual(p.shape, None)
        self.assertEqual(p.dim, 0)
        self.assertEqual(p.array_size, 1)
        self.assertEqual(p.upper_bound, 1.0)
        self.assertEqual(p.lower_bound, 0.0)
        self.assertEqual(p.ubound, 1.0)
        self.assertEqual(p.lbound, 0.0)
        print(p.gen_values(2, 'interval'))
        self.assertTrue(np.allclose(p.gen_values(3, 'interval'), [0.0, 0.5, 1.0]))
        gen_values = p.gen_values(8, 'rand')
        self.assertEqual(len(gen_values), 8)
        self.assertTrue(all([(0.0 <= item <= 1.0) for item in gen_values]))
        self.assertIsNone(p.value)
        p.set_value(0.5)
        self.assertEqual(p.value, 0.5)
        p.value = 0.75
        self.assertEqual(p.get_value(), 0.75)
        self.assertEqual(str(p), "Parameter((0.0, 1.0), 'float')")

        self.assertRaises(TypeError, p.set_value, 'wrong_type')
        self.assertRaises(ValueError, p.set_value, 1.5)

        self.assertRaises(TypeError, p.enum_values)

        p = Parameter(('a', 'b'), name='par3')
        self.assertEqual(p.name, 'par3')
        self.assertEqual(p.par_type, 'enum')
        self.assertEqual(p.par_range, ('a', 'b'))
        self.assertEqual(p.count, 2)
        self.assertEqual(p.size, 2)
        self.assertEqual(p.shape, None)
        self.assertEqual(p.dim, 0)
        self.assertEqual(p.array_size, 1)
        self.assertEqual(p.ubound, 'b')
        self.assertEqual(p.lbound, 'a')
        self.assertEqual(p.upper_bound, 'b')
        self.assertEqual(p.lower_bound, 'a')
        self.assertEqual(list(p.gen_values(2, 'int')), ['a', 'b'])
        values = list(p.gen_values(3, 'rand'))
        self.assertEqual(len(values), 3)
        self.assertTrue(all([item in ('a', 'b') for item in values]))
        self.assertTrue(all([item in p for item in values]))
        self.assertEqual(list(p.enum_values()), ['a', 'b'])
        self.assertTrue('a' in p)

        # test parameter with array values
        p = Parameter((0, 10), name='arr_par', par_type='array[4, 5]')
        self.assertEqual(p.name, 'arr_par')
        self.assertEqual(p.par_type, 'int_array')
        self.assertEqual(p.par_range, (0, 10))
        self.assertEqual(p.shape, (4, 5))
        self.assertEqual(p.dim, 2)
        self.assertEqual(p.array_size, 20)
        self.assertEqual(p.count, 8667208279016151025)
        self.assertEqual(p.size, 8667208279016151025)
        self.assertEqual(p.ubound, 10)
        self.assertEqual(p.lbound, 0)
        self.assertEqual(p.upper_bound, 10)
        self.assertEqual(p.lower_bound, 0)
        for val in p.gen_values(5, 'int'):
            self.assertEqual(val.shape, (4, 5))
            self.assertTrue(np.all((0 <= val) & (val <= 10)))
            self.assertTrue(val in p)
        for val in p.gen_values(5, 'rand'):
            self.assertEqual(val.shape, (4, 5))
            self.assertTrue(np.all((0 <= val) & (val <= 10)))
            self.assertTrue(val in p)

        value1 = np.random.randint(0, 11, size=(4, 5))
        p.set_value(value1)
        self.assertTrue(np.array_equal(p.value, value1))
        self.assertTrue(value1 in p)
        value2 = np.random.randint(10, 15, size=(4, 5))
        self.assertFalse(value2 in p)
        self.assertRaises(ValueError, p.set_value, value2)
        value3 = np.random.randint(0, 11, size=(4, 4))
        self.assertFalse(value3 in p)
        self.assertFalse(5 in p)
        self.assertFalse('a' in p)
        self.assertRaises(ValueError, p.set_value, value3)

        self.assertRaises(ArithmeticError, p.enum_values)

        p = Parameter((0.0, 1.5), name='float_arr_par', par_type='array[3, 5]')
        self.assertEqual(p.par_type, 'float_array')
        self.assertEqual(p.name, 'float_arr_par')
        self.assertEqual(p.par_range, (0.0, 1.5))
        self.assertEqual(p.shape, (3, 5))
        self.assertEqual(p.dim, 2)
        self.assertEqual(p.array_size, 15)
        self.assertEqual(p.count, np.inf)
        self.assertAlmostEqual(p.size, 437.8938903808594)

        for val in p.gen_values(5, 'int'):
            self.assertEqual(val.shape, (3, 5))
            print(val)
            self.assertTrue(np.all((0 <= val) & (val <= 1.5)))
            self.assertTrue(val in p)
        for val in p.gen_values(5, 'rand'):
            self.assertEqual(val.shape, (3, 5))
            print(val)
            self.assertTrue(np.all((0 <= val) & (val <= 1.5)))
            self.assertTrue(val in p)

        p = Parameter((1, 10), name='int_arr_par', par_type='int[3, 5]')
        self.assertEqual(p.par_type, 'int_array')
        p = Parameter(10, name='int_arr_par', par_type='int[3, 5]')
        self.assertEqual(p.par_type, 'int_array')
        p = Parameter((0, 10), name='float_arr_par', par_type='float[3, 5]')
        self.assertEqual(p.par_type, 'float_array')
        p = Parameter(1.5, name='float_arr_par', par_type='float[3, 5, 5]')
        self.assertEqual(p.par_type, 'float_array')
        self.assertEqual(p.shape, (3, 5, 5))
        p = Parameter((1, 10), name='int_arr_par', par_type='int[3,]')
        self.assertEqual(p.par_type, 'int_array')

        self.assertRaises(ValueError, Parameter, 15, par_type='int[]')

        p = Parameter((1, 2, 3), name='par4')
        self.assertEqual(p.name, 'par4')
        self.assertEqual(p.par_type, 'enum')
        self.assertEqual(str(p), "Parameter((1, 2, 3), 'enum')")

        p = Parameter(3, name='par5')
        self.assertEqual(p.name, 'par5')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.par_range, (0, 3))

        p = Parameter(3.5, name='par6')
        self.assertEqual(p.name, 'par6')
        self.assertEqual(p.par_type, 'float')
        self.assertEqual(p.par_range, (0.0, 3.5))

        p = Parameter('a', name='par7')
        self.assertEqual(p.name, 'par7')
        self.assertEqual(p.par_type, 'enum')
        self.assertEqual(p.par_range, ('a',))

        p = Parameter(5, par_type='discr')
        self.assertEqual(p.name, '')
        self.assertEqual(p.par_type, 'int')

        self.assertRaises(ValueError, Parameter, 5, par_type='wrong_type')

        p = Parameter((0, 10), name='par8', par_type='int', value=5)
        self.assertEqual(p.name, 'par8')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.value, 5)

        p = Parameter((0.0, 8.0), name='par9', par_type='int')
        self.assertEqual(p.name, 'par9')
        self.assertEqual(p.par_type, 'int')

        self.assertRaises(ValueError, Parameter, (0.0, 8.0), name='par10', par_type='int', value=9.5)

        p = Parameter((10, -10), name='par10', par_type='int')
        self.assertEqual(p.name, 'par10')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.par_range, (-10, 10))
        self.assertEqual(p.count, 21)
        self.assertEqual(p.size, 21)
        self.assertEqual(p.ubound, 10)
        values = p.gen_values(5, 'interval')
        self.assertTrue(np.allclose(values, [-10, -5, 0, 5, 10]))

        p = Parameter((-10.5, 10.5), par_type='int')
        self.assertEqual(p.name, '')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.par_range, (-10, 10))

        # test other valid parameter initializations
        p = Parameter((10, '20'), name='par16', par_type='int')
        p = Parameter(('20',), name='par16', par_type='int')
        p = Parameter('20', name='par16')
        p = Parameter('a')
        p = Parameter('a, b, b, c')
        p = Parameter(['a', 'b', 'b', 'c'])

        # test wrong parameter initialization
        self.assertRaises(ValueError, Parameter, (10, -10), name='par11', par_type='int', value=15)
        self.assertRaises(ValueError, Parameter, (10, -10), name='par12', par_type='arr')
        self.assertRaises(ValueError, Parameter, (10, -10), name='par13', par_type='enum[2,3,4]')
        self.assertRaises(ValueError, Parameter, (10, -10), name='par14', par_type='int[2,3][2,3,4]')
        self.assertRaises(ValueError, Parameter, (10, -10), name='par15', par_type='wrong type')
        self.assertRaises(ValueError, Parameter, ('a', 'a20', 4, 4, 5), name='par16', par_type='int')
        self.assertRaises(ValueError, Parameter, (10, -10), name='par12', par_type='arr[-2, 3]')
        self.assertRaises(ValueError, Parameter, (10, -10), name='par12', par_type='arr[-2, "a"]')
        self.assertRaises(ValueError, Parameter, (10, -10), name='par12', par_type='arr[-2, 3.35]')

    def test_gen_values(self):
        p = Parameter((0, 10), name='par11', par_type='int')
        values = p.gen_values(6, 'interval')
        self.assertTrue(np.allclose(values, [0, 2, 4, 6, 8, 10]))
        values = p.gen_values(5, 'rand')
        self.assertEqual(len(values), 5)
        self.assertTrue(all([(0 <= item <= 10) for item in values]))

        p = Parameter((0.0, 10.0), name='par12', par_type='float')
        values = p.gen_values(5, 'interval')
        self.assertTrue(np.allclose(values, [0.0, 2.5, 5.0, 7.5, 10]))
        values = p.gen_values(5, 'rand')
        self.assertEqual(len(values), 5)
        self.assertTrue(all([(0.0 <= item <= 10.0) for item in values]))

        p = Parameter(('a', 'b', 'c', 'd', 'e', 'f', 'g'), name='par13', par_type='enum')
        values = p.gen_values(3, how='int')
        self.assertEqual(values, ['a', 'd', 'g'])
        values = p.gen_values(3, how='rand')
        self.assertEqual(len(values), 3)
        self.assertTrue(all([item in ('a', 'b', 'c', 'd', 'e', 'f', 'g') for item in values]))

        self.assertRaises(ValueError, p.gen_values, 0, 'int')
        self.assertRaises(ValueError, p.gen_values, -1, 'int')
        self.assertRaises(ValueError, p.gen_values, 0.35, 'int')
        self.assertRaises(ValueError, p.gen_values, 0, 'rand')
        self.assertRaises(ValueError, p.gen_values, -1, 'rand')
        self.assertRaises(ValueError, p.gen_values, 0.35, 'rand')
        self.assertRaises(TypeError, p.gen_values, 5, 15)
        self.assertRaises(KeyError, p.gen_values, 5, 'wrong_how')

    def test_get_and_set_values(self):
        p = Parameter((0, 10), name='par14', par_type='int')
        self.assertIsNone(p.value)
        p.set_value(5)
        self.assertEqual(p.value, 5)
        p.value = 7
        self.assertEqual(p.value, 7)
        self.assertEqual(p.get_value(), 7)

        self.assertRaises(TypeError, p.set_value, 'wrong_type')
        self.assertRaises(ValueError, p.set_value, 11)

        p = Parameter((0.0, 10.0), name='par15', par_type='float')
        self.assertIsNone(p.value)
        p.set_value(5.5)
        self.assertEqual(p.value, 5.5)
        p.value = 7.25
        self.assertEqual(p.value, 7.25)
        self.assertEqual(p.get_value(), 7.25)

        self.assertRaises(TypeError, p.set_value, 'wrong_type')
        self.assertRaises(ValueError, p.set_value, 11.5)

        p = Parameter(('a', 'b', 'c'), name='par16', par_type='enum')
        self.assertIsNone(p.value)
        p.set_value('b')
        self.assertEqual(p.value, 'b')
        p.value = 'c'
        self.assertEqual(p.value, 'c')
        self.assertEqual(p.get_value(), 'c')

        self.assertRaises(ValueError, p.set_value, 5)
        self.assertRaises(ValueError, p.set_value, 'd')

        p = Parameter((0, 10), name='par17', par_type='array[2,3]')
        self.assertIsNone(p.value)
        value1 = np.random.randint(0, 11, size=(2, 3))
        p.set_value(value1)
        self.assertTrue(np.array_equal(p.value, value1))
        value2 = np.random.randint(0, 11, size=(2, 3))
        p.value = value2
        self.assertTrue(np.array_equal(p.value, value2))
        self.assertTrue(np.array_equal(p.get_value(), value2))

        value3 = np.random.randint(11, 15, size=(2, 3))
        self.assertRaises(ValueError, p.set_value, value3)
        value4 = np.random.randint(0, 11, size=(2, 2))
        self.assertRaises(ValueError, p.set_value, value4)

    def test_signal_blend(self):
        self.assertEqual(blender_parser('s0 & 1'), ['&', '1', 's0'])
        self.assertEqual(blender_parser('s0 or 1'), ['or', '1', 's0'])
        self.assertEqual(blender_parser('s0 & s1 | s2'), ['|', 's2', '&', 's1', 's0'])
        blender = blender_parser('s0 & s1 | s2')
        self.assertEqual(signal_blend([1, 1, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 1, 0], blender), 1)
        self.assertEqual(signal_blend([0, 1, 1], blender), 1)
        self.assertEqual(signal_blend([0, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 0], blender), 0)
        self.assertEqual(signal_blend([0, 1, 0], blender), 0)
        self.assertEqual(signal_blend([0, 0, 0], blender), 0)
        # parse: '0 & ( 1 | 2 )'
        self.assertEqual(blender_parser('s0 & ( s1 | s2 )'), ['&', '|', 's2', 's1', 's0'])
        blender = blender_parser('s0 & ( s1 | s2 )')
        self.assertEqual(signal_blend([1, 1, 1], blender), 1)
        self.assertEqual(signal_blend([1, 0, 1], blender), 1)
        self.assertEqual(signal_blend([1, 1, 0], blender), 1)
        self.assertEqual(signal_blend([0, 1, 1], blender), 0)
        self.assertEqual(signal_blend([0, 0, 1], blender), 0)
        self.assertEqual(signal_blend([1, 0, 0], blender), 0)
        self.assertEqual(signal_blend([0, 1, 0], blender), 0)
        self.assertEqual(signal_blend([0, 0, 0], blender), 0)
        # parse: '(1-2) and 3 + ~0'
        self.assertEqual(blender_parser('(s1-s2)/s3 + s0'), ['+', 's0', '/', 's3', '-', 's2', 's1'])
        blender = blender_parser('(s1-s2)/s3 + s0')
        self.assertEqual(signal_blend([5, 9, 1, 4], blender), 7)
        # parse: '(1-2)/3 + 0'
        self.assertEqual(blender_parser('(s1-s2)/s3 + s0'), ['+', 's0', '/', 's3', '-', 's2', 's1'])
        blender = blender_parser('(s1-s2)/s3 + s0')
        self.assertEqual(signal_blend([5, 9, 1, 4], blender), 7)
        # pars: '(0*1/2*(3+4))+5*(6+7)-8'
        self.assertEqual(blender_parser('(s0*s1/s2*(s3+s4))+s5*(s6+s7)-s8'),
                         ['-', 's8', '+', '*', '+', 's7', 's6', 's5', '*', '+', 's4', 's3', '/', 's2', '*', 's1', 's0'])
        blender = blender_parser('(s0*s1/s2*(s3+s4))+s5*(s6+s7)-s8')
        self.assertEqual(signal_blend([1, 1, 1, 1, 1, 1, 1, 1, 1], blender), 3)
        self.assertEqual(signal_blend([2, 1, 4, 3, 5, 5, 2, 2, 10], blender), 14)
        # parse: '0/max(2,1,3 + 5)+4'
        self.assertEqual(blender_parser('s0/max(s2,s1,s3 + s5)+s4'),
                         ['+', 's4', '/', 'max(3)', '+', 's5', 's3', 's1', 's2', 's0'])
        blender = blender_parser('s0/max(s2,s1,s3 + 5)+s4')
        self.assertEqual(signal_blend([8.0, 4, 3, 5.0, 0.125, 5], blender), 0.925)
        self.assertEqual(signal_blend([2, 1, 4, 3, 5, 5, 2, 2, 10], blender), 5.25)

        print('speed test')
        import time
        st = time.time()
        blender = blender_parser('s0+max(s1,s2,(s3+s4)*s5, max(s6, (s7+s8)*s9), s10-s11) * (s12+s13)')
        res = []
        for i in range(10000):
            res = signal_blend([1, 1, 2, 3, 4, 5, 3, 4, 5, 6, 7, 8, 2, 3], blender)
        et = time.time()
        print(f'total time for RPN processing: {et - st}, got result: {res}')

        blender = blender_parser("s0 + s1 * s2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 7)
        blender = blender_parser("(s0 + s1) * s2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        blender = blender_parser("(s0+s1) * s2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        blender = blender_parser("(s0 + s1)   * s2")
        self.assertEqual(signal_blend([1, 2, 3], blender), 9)
        blender = blender_parser("(s0-s1)/s2 + s3")
        print(f'RPN of notation: "(s0-s1)/s2 + s3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 2, 3, 0.0], blender), -0.33333333)
        blender = blender_parser("-(s0-s1)/s2 + s3")
        print(f'RPN of notation: "-(s0-s1)/s2 + s3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 2, 3, 0.0], blender), 0.33333333)
        blender = blender_parser("~(0-1)/s2 + s3")
        print(f'RPN of notation: "~(s0-s1)/s2 + s3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 2, 3, 0.0], blender), 0.33333333)
        blender = blender_parser("s0 + s1 / s2")
        print(f'RPN of notation: "0 + 1 / 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, math.pi, 4], blender), 1.78539816)
        blender = blender_parser("(s0 + s1) / s2")
        print(f'RPN of notation: "(0 + 1) / 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(signal_blend([1, 2, 3], blender), 1)
        blender = blender_parser("(s0 + s1 * s2) / s3")
        print(f'RPN of notation: "(0 + 1 * 2) / 3" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([3, math.e, 10, 10], blender), 3.0182818284590454)
        blender = blender_parser("s0 / s1 * s2")
        print(f'RPN of notation: "0 / 1 * 2" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(signal_blend([1, 3, 6], blender), 2)
        blender = blender_parser("(s0 - s1 + s2) * s4")
        print(f'RPN of notation: "(0 - 1 + 2) * 4" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([1, 1, -1, np.nan, math.pi], blender), -3.141592653589793)
        blender = blender_parser("s0 * s1")
        print(f'RPN of notation: "0 * 1" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertAlmostEqual(signal_blend([math.pi, math.e], blender), 8.539734222673566)

        blender = blender_parser('abs(s3-sqrt(s2) /  cos(s1))')
        print(f'RPN of notation: "abs(3-sqrt(2) /  cos(1))" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['abs(1)', '-', '/', 'cos(1)', 's1', 'sqrt(1)', 's2', 's3'])
        blender = blender_parser('s0/max(s2,s1,s3 + s5)+s4')
        print(f'RPN of notation: "0/max(2,1,3 + 5)+4" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', 's4', '/', 'max(3)', '+', 's5', 's3', 's1', 's2', 's0'])

        blender = blender_parser('s1 + sum(s1,s2,s3+s3, sum(s1, s2) + s3) *s5')
        print(f'RPN of notation: "1 + sum(1,2,3+3, sum(1, 2) + 3) *5" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', '*', 's5', 'sum(4)', '+', 's3', 'sum(2)', 's2', 's1',
                                   '+', 's3', 's3', 's2', 's1', 's1'])
        blender = blender_parser('s1+sum(1,2,(s3+s5)*s4, sum(s3, (4+s5)*s6), s7-s8) * (s2+s3)')
        print(f'RPN of notation: "1+sum(1,2,(3+5)*4, sum(3, (4+5)*6), 7-8) * (2+3)" is:\n'
              f'{" ".join(blender[::-1])}')
        self.assertEqual(blender, ['+', '*', '+', 's3', 's2', 'sum(5)', '-', 's8', 's7',
                                   'sum(2)', '*', 's6', '+', 's5', '4', 's3', '*', 's4',
                                   '+', 's5', 's3', '2', '1', 's1'])

    def test_tokenizer(self):
        self.assertListEqual(_exp_to_token('s1+s1'),
                             ['s1', '+', 's1'])
        print(_exp_to_token('s1+s1'))
        self.assertListEqual(_exp_to_token('1+1'),
                             ['1', '+', '1'])
        print(_exp_to_token('1+1'))
        self.assertListEqual(_exp_to_token('1 & 1'),
                             ['1', '&', '1'])
        print(_exp_to_token('1&1'))
        self.assertListEqual(_exp_to_token('1 and 1'),
                             ['1', 'and', '1'])
        print(_exp_to_token('1 and 1'))
        self.assertListEqual(_exp_to_token('-1 and 1'),
                             ['-1', 'and', '1'])
        print(_exp_to_token('s0 and s1'))
        self.assertListEqual(_exp_to_token('s0 or s1'),
                             ['s0', 'or', 's1'])
        print(_exp_to_token('1 and 1'))
        self.assertListEqual(_exp_to_token('1 or 1'),
                             ['1', 'or', '1'])
        print(_exp_to_token('1 or 1'))
        self.assertListEqual(_exp_to_token('(1 - 1 + -1) * pi'),
                             ['(', '1', '-', '1', '+', '-1', ')', '*', 'pi'])
        print(_exp_to_token('(1 - 1 + -1) * pi'))
        self.assertListEqual(_exp_to_token('(s1 - s1 + -1) * pi'),
                             ['(', 's1', '-', 's1', '+', '-1', ')', '*', 'pi'])
        print(_exp_to_token('(s1 - s1 + -1) * pi'))
        self.assertListEqual(_exp_to_token('abs(5-sqrt(2) /  cos(pi))'),
                             ['abs(', '5', '-', 'sqrt(', '2', ')', '/', 'cos(', 'pi', ')', ')'])
        print(_exp_to_token('abs(5-sqrt(2) /  cos(pi))'))
        self.assertListEqual(_exp_to_token('abs(s5-sqrt(s2) /  cos(pi))'),
                             ['abs(', 's5', '-', 'sqrt(', 's2', ')', '/', 'cos(', 'pi', ')', ')'])
        print(_exp_to_token('abs(s5-sqrt(s2) /  cos(pi))'))
        self.assertListEqual(_exp_to_token('sin(pi) + 2.14'),
                             ['sin(', 'pi', ')', '+', '2.14'])
        print(_exp_to_token('sin(pi) + 2.14'))
        self.assertListEqual(_exp_to_token('-sin(pi) + 2.14'),
                             ['-1', '*', 'sin(', 'pi', ')', '+', '2.14'])
        print(_exp_to_token('-sin(pi) + 2.14'))
        self.assertListEqual(_exp_to_token('(1-2)/3.0 + 0.0000'),
                             ['(', '1', '-', '2', ')', '/', '3.0', '+', '0.0000'])
        print(_exp_to_token('(1-2)/3.0 + 0.0000'))
        self.assertListEqual(_exp_to_token('-(1. + .2) * max(1, 3, 5)'),
                             ['-1', '*', '(', '1.', '+', '.2', ')', '*', 'max(', '1', ',', '3', ',', '5', ')'])
        print(_exp_to_token('-(1. + .2) * max(1, 3, 5)'))
        self.assertListEqual(_exp_to_token('(x + e * 10) / 10'),
                             ['(', 'x', '+', 'e', '*', '10', ')', '/', '10'])
        print(_exp_to_token('(x + e * 10) / 10'))
        self.assertListEqual(_exp_to_token('8.2/((-.1+abs3(3,4,5))*0.12)'),
                             ['8.2', '/', '(', '(', '-.1', '+', 'abs3(', '3', ',', '4', ',', '5', ')', ')', '*', '0.12',
                              ')'])
        print(_exp_to_token('8.2/((-.1+abs3(3,4,5))*0.12)'))
        self.assertListEqual(_exp_to_token('8.2/abs3(3,4,25.34 + 5)*0.12'),
                             ['8.2', '/', 'abs3(', '3', ',', '4', ',', '25.34', '+', '5', ')', '*', '0.12'])
        print(_exp_to_token('8.2/abs3(3,4,25.34 + 5)*0.12'))
        self.assertListEqual(_exp_to_token('abs(-1.14)+power(2, 3)and log(3.14)'),
                             ['abs(', '-1.14', ')', '+', 'power(', '2', ',', '3', ')', 'and', 'log(', '3.14', ')'])
        print(_exp_to_token('abs(-1.14)+power(2, 3)and log(3.14)'))
        self.assertListEqual(_exp_to_token('strength_1.25(0, 1, 2)'),
                             ['strength_1.25(', '0', ',', '1', ',', '2', ')'])
        print(_exp_to_token('strength_1.25(0, 1, 2)'))
        self.assertListEqual(_exp_to_token('avg_pos_3_1.25(0, 1,2)'),
                             ['avg_pos_3_1.25(', '0', ',', '1', ',', '2', ')'])
        print(_exp_to_token('avg_pos_3_1.25(0, 1,2)'))
        self.assertListEqual(_exp_to_token('clip_-1_1(pos_5_0.2(0, 1, 2, 3, 4))'),
                             ['clip_-1_1(', 'pos_5_0.2(', '0', ',', '1', ',', '2', ',', '3', ',', '4', ')', ')'])
        print(_exp_to_token('clip_-1_1(pos_5_0.2(0, 1, 2, 3, 4))'))

    def test_all_blending_funcs(self):
        """ 测试其他信号组合函数是否正常工作"""
        # 生成五个示例交易信号
        signal0 = np.array([[0.12, 0.35, 0.11],
                            [0.81, 0.22, 0.29],
                            [0.86, 0.47, 0.29],
                            [0.46, 0.81, 0.60],
                            [0.42, 0.55, 0.74]])
        signal1 = np.array([[0.94, 0.66, 0.69],
                            [0.85, 0.30, 0.65],
                            [0.87, 0.06, 0.24],
                            [0.73, 0.20, 0.19],
                            [0.43, 0.18, 0.44]])
        signal2 = np.array([[0.24, 0.81, 0.44],
                            [0.66, 0.92, 0.99],
                            [0.18, 0.17, 0.11],
                            [0.48, 0.57, 0.55],
                            [0.37, 0.66, 0.01]])
        signal3 = np.array([[0.92, 0.88, 0.16],
                            [0.89, 0.79, 0.27],
                            [0.48, 0.77, 0.20],
                            [0.43, 0.33, 0.25],
                            [0.90, 0.30, 0.49]])
        signal4 = np.array([[0.05, 0.17, 0.30],
                            [0.16, 0.62, 0.61],
                            [0.52, 0.83, 0.57],
                            [0.16, 0.36, 0.28],
                            [0.99, 0.57, 0.04]])
        # 将示例信号组合为交易信号组，与operator输出形式相同
        signals = [signal0, signal1, signal2, signal3, signal4]

        # 开始测试blender functions
        print('\ntest average functions')
        blender_exp = 'avg(s0, s1, s2, s3, s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.454, 0.574, 0.340],
                           [0.674, 0.570, 0.562],
                           [0.582, 0.460, 0.282],
                           [0.452, 0.454, 0.374],
                           [0.622, 0.452, 0.344]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest comparison functions')
        blender_exp = 'combo(s0, s1, s2) + min(s0, s1,s2)-max(s2, s3, s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.50,  1.29,  0.91],
                           [2.09,  0.74,  1.23],
                           [1.57, -0.07,  0.18],
                           [1.65,  1.21,  0.98],
                           [0.60,  0.91,  0.71]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest mathematical functions')
        blender_exp = 'abs(s0) + ceil(s1) * pow(s0, s1) + floor(s2+s3+s4) - exp(s3) and log(s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[8.77344165, 6.12214254, 1.74092762],
                           [7.10858499, 3.90823377, 2.38476921],
                           [3.79382222, 2.82813777, 1.71955085],
                           [4.84445021, 4.18981584, 4.14202468],
                           [3.13336769, 3.20675832, 6.87013820]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function strength')
        blender_exp = 'strength_1.35(s0, s1, s2)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0., 1., 0.],
                           [1., 1., 1.],
                           [1., 0., 0.],
                           [1., 1., 0.],
                           [0., 1., 0.]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function position')
        blender_exp = 'pos_3_0.5(s0, s1, s2, s3, s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0., 1., 0.],
                           [1., 1., 1.],
                           [1., 0., 0.],
                           [0., 0., 0.],
                           [0., 1., 0.]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function clip')
        blender_exp = 'clip_-1_0.8(pos_5_0.2(s0, s1, s2, s3, s4))'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.0, 0.0, 0.0],
                           [0.0, 0.8, 0.8],
                           [0.0, 0.0, 0.0],
                           [0.0, 0.8, 0.0],
                           [0.8, 0.0, 0.0]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function avg position')
        blender_exp = 'avgpos_3_0.5(s0, s1, s2, s3, s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.000, 0.574, 0.000],
                           [0.674, 0.570, 0.562],
                           [0.582, 0.000, 0.000],
                           [0.000, 0.000, 0.000],
                           [0.000, 0.452, 0.000]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function unify')
        blender_exp = 'unify(avgpos_3_0.5(s0, s1, s2, s3, s4))'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.00000000, 1.00000000, 0.00000000],
                           [0.37320044, 0.31561462, 0.31118494],
                           [1.00000000, 0.00000000, 0.00000000],
                           [0.00000000, 0.00000000, 0.00000000],
                           [0.00000000, 1.00000000, 0.00000000]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        print('\ntest signal combination function with pure numbers')
        blender_exp = 'avgpos_3_0.5(s0, 1.5*s1, 2*s2, 0.5*s3, 2+s4)'
        blender = blender_parser(blender_exp)
        res = signal_blend(signals, blender)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        target = np.array([[0.000, 1.114, 0.881],
                           [1.202, 0.000, 1.198],
                           [1.057, 0.000, 0.000],
                           [0.978, 0.955, 0.878],
                           [1.049, 0.972, 0.741]])

        hit = np.allclose(res, target)
        self.assertTrue(hit)

        # test human_blender function:
        print('\ntest human_blender function')
        strategy_ids = ['MACD', 'DMA', 'CROSSLINE', 'TRIX', 'KDJ']
        blender_exp = 'avgpos_3_0.5(s0, s1, s2, s3, s4)'
        res = human_blender(blender_exp, strategy_ids)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        self.assertEqual(res, 'avgpos_3_0.5(MACD, DMA, CROSSLINE, TRIX, KDJ)')

        blender_exp = 'max(s0, s1, s2)+s3*s4'
        res = human_blender(blender_exp, strategy_ids)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        self.assertEqual(res, 'max(MACD, DMA, CROSSLINE) + TRIX * KDJ')

        blender_exp = 'max(s0, s1/s0)+s1and0.5*s4'
        res = human_blender(blender_exp, strategy_ids)
        print(f'blended signals with blender "{blender_exp}" is \n{res}')
        self.assertEqual(res, 'max(MACD, DMA / MACD) + DMA and 0.5 * KDJ')

        blender_exp = 'max(s0, s1/s0)+s1^0.5*s6'
        self.assertRaises(IndexError, human_blender, blender_exp, strategy_ids)


if __name__ == '__main__':
    unittest.main()