# coding=utf-8
# ======================================
# File:     test_space.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all optimizable
#   parameter space related functions.
# ======================================
import unittest

import numpy as np
from numpy import int64
import itertools

from qteasy.space import Space, Parameter, space_around_centre, ResultPool


class TestSpace(unittest.TestCase):
    def test_creation(self):
        """
            test if creation of space object is fine
        """
        # first group of inputs, output Space with two discr axis from [0,10]
        print('testing space objects\n')
        pars_list = [((0, 10), (0, 10)),
                     ([0, 10], [0, 10])]

        types_list = ['int',
                      ['int', 'int']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            print(p)
            s = Space(*p[0], par_types=p[1])
            b = s.boes
            t = s.types
            print(s, t)
            self.assertIsInstance(s, Space)
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['int', 'int'], 'types incorrect')

        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = ['foo, bar',
                      ['foo', 'bar']]

        # test invalid par types
        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            self.assertRaises(ValueError, Space, *p[0], par_types=p[1])

        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = [['int', 'enumerate']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            s = Space(*p[0], par_types=p[1])
            b = s.boes
            t = s.types
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['int', 'enum'], 'types incorrect')

        pars_list = [(0., 10), (0, 10)]
        s = Space(*pars_list, par_types=None)
        self.assertEqual(s.types, ['float', 'int'])
        self.assertEqual(s.dim, 2)
        self.assertEqual(s.size, (10.0, 11))
        self.assertEqual(s.shape, (np.inf, 11))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0., 10), (0, 10)])

        pars_list = [(0., 10), (0, 10)]
        s = Space(*pars_list, par_types=['conti', 'enum'])
        self.assertEqual(s.types, ['float', 'enum'])
        self.assertEqual(s.dim, 2)
        self.assertEqual(s.size, (10.0, 2))
        self.assertEqual(s.shape, (np.inf, 2))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0., 10), (0, 10)])

        pars_list = [(1, 2), (2, 3), (3, 4)]
        s = Space(*pars_list)
        self.assertEqual(s.types, ['int', 'int', 'int'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (2, 2, 2))
        self.assertEqual(s.shape, (2, 2, 2))
        self.assertEqual(s.count, 8)
        self.assertEqual(s.boes, [(1, 2), (2, 3), (3, 4)])

        pars_list = [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
        s = Space(*pars_list)
        self.assertEqual(s.types, ['enum', 'enum', 'enum'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (3, 3, 3))
        self.assertEqual(s.shape, (3, 3, 3))
        self.assertEqual(s.count, 27)
        self.assertEqual(s.boes, [(1, 2, 3), (2, 3, 4), (3, 4, 5)])

        pars_list = [((1, 2, 3), (2, 3, 4), (3, 4, 5))]
        s = Space(*pars_list)
        self.assertEqual(s.types, ['enum'])
        self.assertEqual(s.dim, 1)
        self.assertEqual(s.size, (3,))
        self.assertEqual(s.shape, (3,))
        self.assertEqual(s.count, 3)

        pars_list = ((1, 2, 3), (2, 3, 4), (3, 4, 5))
        s = Space(*pars_list)
        self.assertEqual(s.types, ['enum', 'enum', 'enum'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (3, 3, 3))
        self.assertEqual(s.shape, (3, 3, 3))
        self.assertEqual(s.count, 27)
        self.assertEqual(s.boes, [(1, 2, 3), (2, 3, 4), (3, 4, 5)])

        print('testing space_around_centre')
        pars_list = ((0, 10), (0, 10))
        s = Space(*pars_list, par_types=None)
        centre = (5, 5)
        distance = 2
        s2 = space_around_centre(s, centre, distance)
        self.assertEqual(s2.types, ['int', 'int'])
        self.assertEqual(s2.dim, 2)
        self.assertEqual(s2.size, (5, 5))
        self.assertEqual(s2.shape, (5, 5))
        self.assertEqual(s2.count, 25)
        self.assertEqual(s2.boes, [(3, 7), (3, 7)])

        pars_space = ((0., 10.), (0, 10), (0., 10.))
        s = Space(*pars_space, par_types=None)
        centre = (5, 5, 5)
        distance = 2
        s2 = space_around_centre(s, centre, distance)
        self.assertEqual(s2.types, ['float', 'int', 'float'])
        self.assertEqual(s2.dim, 3)
        self.assertEqual(s2.size, (4.0, 5, 4.0))
        self.assertEqual(s2.shape, (np.inf, 5, np.inf))
        self.assertEqual(s2.count, np.inf)
        self.assertEqual(s2.boes, [(3, 7), (3, 7), (3, 7)])

        # test creating Space from Parameter objects
        param1 = Parameter((0, 10), par_type='int')
        param2 = Parameter((0., 10.), par_type='conti')
        param3 = Parameter((1, 2, 3), par_type='enum')
        s = Space(param1, param2, param3)
        self.assertIsInstance(s, Space)
        self.assertEqual(s.types, ['int', 'float', 'enum'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (11, 10.0, 3))
        self.assertEqual(s.shape, (11, np.inf, 3))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0, 10), (0., 10.), (1, 2, 3)])

    def test_extract(self):
        """

        :return:
        """
        pars_list = [(0, 10), (0, 10)]
        types_list = ['int', 'int']
        s = Space(*pars_list, par_types=types_list)
        extracted_int, count = s.extract(16, 'interval')
        extracted_int_list = list(extracted_int)
        print('extracted int\n', extracted_int_list)
        self.assertEqual(count, 16, 'extraction count wrong!')
        self.assertEqual(extracted_int_list, [(0, 0), (0, 3), (0, 6), (0, 10), (3, 0), (3, 3),
                                              (3, 6), (3, 10), (6, 0), (6, 3), (6, 6), (6, 10),
                                              (10, 0), (10, 3), (10, 6), (10, 10)],
                         'space extraction wrong!')
        extracted_rand, count = s.extract(10, 'rand')
        extracted_rand_list = list(extracted_rand)
        self.assertEqual(count, 10, 'extraction count wrong!')
        print('extracted rand\n', extracted_rand_list)
        for point in list(extracted_rand_list):
            self.assertEqual(len(point), 2)
            self.assertLessEqual(point[0], 10)
            self.assertGreaterEqual(point[0], 0)
            self.assertLessEqual(point[1], 10)
            self.assertGreaterEqual(point[1], 0)

        pars_list = [(0., 10), (0, 10)]
        s = Space(*pars_list, par_types=None)
        extracted_int2, count = s.extract(16, 'interval')
        self.assertEqual(count, 16, 'extraction count wrong!')
        extracted_int_list2 = list(extracted_int2)
        self.assertEqual(extracted_int_list2,
                         [(0, 0), (0, 3), (0, 6), (0, 10),
                          (3.3333333333333335, 0),
                          (3.3333333333333335, 3),
                          (3.3333333333333335, 6),
                          (3.3333333333333335, 10),
                          (6.666666666666667, 0),
                          (6.666666666666667, 3),
                          (6.666666666666667, 6),
                          (6.666666666666667, 10),
                          (10, 0), (10, 3), (10, 6), (10, 10)])
        print('extracted int list 2\n', extracted_int_list2)
        self.assertIsInstance(extracted_int_list2[0][0], float)
        self.assertIsInstance(extracted_int_list2[0][1], (int, int64))
        extracted_rand2, count = s.extract(10, 'rand')
        self.assertEqual(count, 10, 'extraction count wrong!')
        extracted_rand_list2 = list(extracted_rand2)
        print('extracted rand list 2:\n', extracted_rand_list2)
        for point in extracted_rand_list2:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], float)
            self.assertLessEqual(point[0], 10)
            self.assertGreaterEqual(point[0], 0)
            self.assertIsInstance(point[1], (int, int64))
            self.assertLessEqual(point[1], 10)
            self.assertGreaterEqual(point[1], 0)

        pars_list = [(0., 10), ('a', 'b')]
        s = Space(*pars_list, par_types=['enum', 'enum'])
        extracted_int3, count = s.extract(4, 'interval')
        self.assertEqual(count, 4, 'extraction count wrong!')
        extracted_int_list3 = list(extracted_int3)
        self.assertEqual(extracted_int_list3, [(0., 'a'), (0., 'b'), (10, 'a'), (10, 'b')],
                         'space extraction wrong!')
        print('extracted int list 3\n', extracted_int_list3)
        self.assertIsInstance(extracted_int_list3[0][0], float)
        self.assertIsInstance(extracted_int_list3[0][1], str)
        extracted_rand3, count = s.extract(3, 'rand')
        self.assertEqual(count, 3, 'extraction count wrong!')
        extracted_rand_list3 = list(extracted_rand3)
        print('extracted rand list 3:\n', extracted_rand_list3)
        for point in extracted_rand_list3:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], (float, int))
            self.assertLessEqual(point[0], 10)
            self.assertGreaterEqual(point[0], 0)
            self.assertIsInstance(point[1], str)
            self.assertIn(point[1], ['a', 'b'])

        pars_list = ((0, 10), (1, 'c'), ('a', 'b'), (1, 14))
        s = Space(pars_list, par_types=['enum'])
        extracted_int4, count = s.extract(1, 'interval')
        self.assertEqual(count, 1, 'extraction count wrong!')
        extracted_int_list4 = list(extracted_int4)
        it = zip(extracted_int_list4, [(0, 10), (1, 'c'), (0, 'b'), (1, 14)])
        for item, item2 in it:
            print(item, item2)
        self.assertTrue(all([tuple(ext_item) == item for ext_item, item in it]))
        print('extracted int list 4\n', extracted_int_list4)
        self.assertIsInstance(extracted_int_list4[0], tuple)
        extracted_rand4, count = s.extract(3, 'rand')
        self.assertEqual(count, 3, 'extraction count wrong!')
        extracted_rand_list4 = list(extracted_rand4)
        print('extracted rand list 4:\n', extracted_rand_list4)
        for point in extracted_rand_list4:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], (int, str))
            self.assertIn(point[0], [0, 1, 'a'])
            self.assertIsInstance(point[1], (int, str))
            self.assertIn(point[1], [10, 14, 'b', 'c'])
            self.assertIn(point, [(0., 10), (1, 'c'), ('a', 'b'), (1, 14)])

        pars_list = ((0, 10), (1, 'c'), ('a', 'b'), (1, 14)), (1, 4)
        s = Space(*pars_list, par_types=['enum', 'discr'])
        extracted_int5, count = s.extract(16, 'interval')
        self.assertEqual(count, 16, 'extraction count wrong!')
        extracted_int_list5 = list(extracted_int5)
        for item, item2 in extracted_int_list5:
            print(item, item2)
        self.assertTrue(all([tuple(ext_item) == item for ext_item, item in it]))
        print('extracted int list 5\n', extracted_int_list5)
        self.assertIsInstance(extracted_int_list5[0], tuple)
        extracted_rand5, count = s.extract(5, 'rand')
        self.assertEqual(count, 5, 'extraction count wrong!')
        extracted_rand_list5 = list(extracted_rand5)
        print('extracted rand list 5:\n', extracted_rand_list5)
        for point in extracted_rand_list5:
            self.assertEqual(len(point), 2)
            self.assertIsInstance(point[0], tuple)
            print(f'type of point[1] is {type(point[1])}')
            self.assertIsInstance(point[1], (int, np.int64))
            self.assertIn(point[0], [(0., 10), (1, 'c'), ('a', 'b'), (1, 14)])

        print(f'test incremental extraction')
        pars_list = ((10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250))
        s = Space(*pars_list)
        ext, count = s.extract(4096, 'interval')
        self.assertEqual(count, 4096)
        points = list(ext)
        # 已经取出所有的点，围绕其中10个点生成十个subspaces
        # 检查是否每个subspace都为Space，是否都在s范围内，使用32生成点集，检查生成数量是否正确
        for point in points[1000:1010]:
            subspace = s.from_point(point, 64)
            self.assertIsInstance(subspace, Space)
            self.assertTrue(subspace in s)
            self.assertEqual(subspace.dim, 6)
            self.assertEqual(subspace.types, ['float', 'float', 'float', 'float', 'float', 'float'])
            ext, count = subspace.extract(1024)
            points = list(ext)
            self.assertGreaterEqual(count, 512)
            self.assertLessEqual(count, 4096)
            print(f'\n---------------------------------'
                  f'\nthe space created around point <{point}> is'
                  f'\n{subspace.boes}'
                  f'\nand extracted {count} points, the first 5 are:'
                  f'\n{points[:5]}')

    def test_axis_extract(self):
        # test param object with conti type
        param = Parameter((0., 5))
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.par_type, 'float')
        self.assertEqual(param.par_range, (0., 5.))
        self.assertEqual(param.count, np.inf)
        self.assertEqual(param.size, 5.0)
        self.assertTrue(np.allclose(param.gen_values(6, 'int'), [0., 1., 2., 3., 4., 5.]))
        self.assertTrue(np.allclose(param.gen_values(11, 'int'), [0., 0.5, 1., 1.5, 2., 2.5, 3., 3.5, 4., 4.5, 5.]))
        extracted = param.gen_values(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(0 <= item <= 5) for item in extracted]))

        # test param object with discrete type
        param = Parameter((1, 5))
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.par_type, 'int')
        self.assertEqual(param.par_range, (1, 5))
        self.assertEqual(param.count, 5)
        self.assertEqual(param.size, 5)
        self.assertTrue(np.allclose(param.gen_values(5, 'int'), [1, 2, 3, 4, 5]))
        self.assertRaises(ValueError, param.gen_values, 0.5, 'int')
        extracted = param.gen_values(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(item in [1, 2, 3, 4, 5]) for item in extracted]))

        # test param object with enumerate type
        param = Parameter((1, 5, 7, 10, 'A', 'F'))
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.par_type, 'enum')
        self.assertEqual(param.par_range, (1, 5, 7, 10, 'A', 'F'))
        self.assertEqual(param.count, 6)
        self.assertEqual(param.size, 6)
        self.assertEqual(param.gen_values(6, 'int'), [1, 5, 7, 10, 'A', 'F'])
        self.assertRaises(ValueError, param.gen_values, 0.5, 'int')
        extracted = param.gen_values(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(item in [1, 5, 7, 10, 'A', 'F']) for item in extracted]))

        # test param object with array type
        param = Parameter((0., 1.), par_type='array[2]')
        self.assertIsInstance(param, Parameter)
        self.assertEqual(param.par_type, 'float_array')
        self.assertEqual(param.par_range, (0., 1.))
        self.assertEqual(param.count, np.inf)
        self.assertEqual(param.size, 1.0)
        vals = param.gen_values(5, 'int')
        self.assertEqual(len(vals), 5)
        for val in vals:
            print(f'generated array value: {val}')
            self.assertTrue(isinstance(val, np.ndarray))
            self.assertEqual(val.shape, (2,))
            self.assertTrue(all([(0.0 <= item <= 1.0) for item in val]))


    def test_from_point(self):
        """测试从一个点生成一个space"""
        # 生成一个space，指定space中的一个点以及distance，生成一个sub-space
        pars_list = [(0., 10), (0, 10)]
        s = Space(*pars_list, par_types=None)
        self.assertEqual(s.types, ['float', 'int'])
        self.assertEqual(s.dim, 2)
        self.assertEqual(s.size, (10., 11))
        self.assertEqual(s.shape, (np.inf, 11))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0., 10), (0, 10)])

        print('create subspace from a point in space')
        p = (3, 3)
        distance = 2
        subspace = s.from_point(p, distance)
        self.assertIsInstance(subspace, Space)
        self.assertEqual(subspace.types, ['float', 'int'])
        self.assertEqual(subspace.dim, 2)
        self.assertEqual(subspace.size, (4.0, 5))
        self.assertEqual(subspace.shape, (np.inf, 5))
        self.assertEqual(subspace.count, np.inf)
        self.assertEqual(subspace.boes, [(1, 5), (1, 5)])

        print('create subspace from a 6 dimensional discrete space')
        s = Space((10, 250), (10, 250), (10, 250), (10, 250), (10, 250), (10, 250))
        p = (15, 200, 150, 150, 150, 150)
        d = 10
        subspace = s.from_point(p, d)
        self.assertIsInstance(subspace, Space)
        self.assertEqual(subspace.types, ['int', 'int', 'int', 'int', 'int', 'int'])
        self.assertEqual(subspace.dim, 6)
        self.assertEqual(subspace.volume, 65345616)
        self.assertEqual(subspace.size, (16, 21, 21, 21, 21, 21))
        self.assertEqual(subspace.shape, (16, 21, 21, 21, 21, 21))
        self.assertEqual(subspace.count, 65345616)
        self.assertEqual(subspace.boes, [(10, 25), (190, 210), (140, 160), (140, 160), (140, 160), (140, 160)])

        print('create subspace from a 6 dimensional continuous space')
        s = Space((10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250))
        p = (15, 200, 150, 150, 150, 150)
        d = 10
        subspace = s.from_point(p, d)
        self.assertIsInstance(subspace, Space)
        self.assertEqual(subspace.types, ['float', 'float', 'float', 'float', 'float', 'float'])
        self.assertEqual(subspace.dim, 6)
        self.assertEqual(subspace.volume, 48000000)
        self.assertEqual(subspace.size, (15.0, 20.0, 20.0, 20.0, 20.0, 20.0))
        self.assertEqual(subspace.shape, (np.inf, np.inf, np.inf, np.inf, np.inf, np.inf))
        self.assertEqual(subspace.count, np.inf)
        self.assertEqual(subspace.boes, [(10, 25), (190, 210), (140, 160), (140, 160), (140, 160), (140, 160)])

        print('create subspace with different distances on each dimension')
        s = Space((10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250))
        p = (15, 200, 150, 150, 150, 150)
        d = [10, 5, 5, 10, 10, 5]
        subspace = s.from_point(p, d)
        self.assertIsInstance(subspace, Space)
        self.assertEqual(subspace.types, ['float', 'float', 'float', 'float', 'float', 'float'])
        self.assertEqual(subspace.dim, 6)
        self.assertEqual(subspace.volume, 6000000)
        self.assertEqual(subspace.size, (15.0, 10.0, 10.0, 20.0, 20.0, 10.0))
        self.assertEqual(subspace.shape, (np.inf, np.inf, np.inf, np.inf, np.inf, np.inf))
        self.assertEqual(subspace.count, np.inf)
        self.assertEqual(subspace.boes, [(10, 25), (195, 205), (145, 155), (140, 160), (140, 160), (145, 155)])

    def test_point_in_space(self):
        sp = Space((0., 10.), (0., 10.), (0., 10.))
        p1 = (5.5, 3.2, 7)
        p2 = (-1, 3, 10)
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')
        self.assertFalse(p2 in sp)
        print(f'point {p2} is not in space {sp}')
        sp = Space((0., 10.), (0., 10.), range(40, 3, -2), par_types=['conti', 'conti', 'enum'])
        p1 = (5.5, 3.2, 8)
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')

        # test array type of point
        sp = Space((0., 10.), (0., 10.), par_types=['array[2]', 'array[2, 2]'])
        p1 = (np.array([5.5, 3.2]), np.array([[1, 2], [3, 4]]))
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')
        p2 = (np.array([5.5, 11]), np.array([[1, 2], [3, 4]]))
        self.assertFalse(p2 in sp)
        print(f'point {p2} is not in space {sp}')

    def test_space_in_space(self):
        print('test if a space is in another space')
        sp = Space((0., 10.), (0., 10.), (0., 10.))
        sp2 = Space((0., 10.), (0., 10.), (0., 10.))
        self.assertTrue(sp2 in sp)
        self.assertTrue(sp in sp2)
        print(f'space {sp2} is in space {sp}\n'
              f'and space {sp} is in space {sp2}\n'
              f'they are equal to each other\n')
        sp2 = Space((0, 5.), (2, 7.), (3., 9.))
        self.assertTrue(sp2 in sp)
        self.assertFalse(sp in sp2)
        print(f'space {sp2} is in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'{sp2} is a sub space of {sp}\n')
        sp2 = Space((0, 5), (2, 7), (3., 9))
        self.assertFalse(sp2 in sp)
        self.assertFalse(sp in sp2)
        print(f'space {sp2} is not in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'they have different types of axes\n')
        sp = Space((0., 10.), (0., 10.), range(40, 3, -2))
        self.assertFalse(sp in sp2)
        self.assertFalse(sp2 in sp)
        print(f'space {sp2} is not in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'they have different types of axes\n')

        # test array type of spaces
        sp = Space((0., 10.), (0., 10.), par_types=['array[2]', 'array[2, 2]'])
        sp2 = Space((0., 5.), (0., 5.), par_types=['array[2]', 'array[2, 2]'])
        self.assertTrue(sp2 in sp)
        print(f'space {sp2} is in space {sp}\n'
              f'space {sp} is a sup space of {sp2}\n')
        # if array dimensions are different, then not in
        sp2 = Space((0., 5.), (0., 5.), par_types=['array[3]', 'array[2, 3, 2]'])
        self.assertFalse(sp2 in sp)
        print(f'space {sp2} is not in space {sp}\n'
              f'space {sp} is not a sup space of {sp2}\n')
        # if array range is larger, then not in
        sp2 = Space((0., 15.), (-5., 5.), par_types=['array[2]', 'array[2, 2]'])
        self.assertFalse(sp2 in sp)
        print(f'space {sp2} is not in space {sp}\n'
              f'space {sp} is not a sup space of {sp2}\n')

    def test_space_around_centre(self):
        sp = Space((0., 10.), (0., 10.), (0., 10.))
        p1 = (5.5, 3.2, 7)
        ssp = space_around_centre(space=sp, centre=p1, radius=1.2)
        print(ssp.boes)
        print('\ntest multiple diameters:')
        self.assertEqual(ssp.boes, [(4.3, 6.7), (2.0, 4.4), (5.8, 8.2)])
        ssp = space_around_centre(space=sp, centre=p1, radius=[1, 2, 1])
        print(ssp.boes)
        self.assertEqual(ssp.boes, [(4.5, 6.5), (1.2000000000000002, 5.2), (6.0, 8.0)])
        print('\ntest points on edge:')
        p2 = (5.5, 3.2, 10)
        ssp = space_around_centre(space=sp, centre=p1, radius=3.9)
        print(ssp.boes)
        self.assertEqual(ssp.boes, [(1.6, 9.4), (0.0, 7.1), (3.1, 10.0)])
        print('\ntest enum spaces')
        sp = Space((0, 100), range(40, 3, -2), par_types=['discr', 'enum'])
        p1 = [34, 12]
        ssp = space_around_centre(space=sp, centre=p1, radius=5, ignore_enums=False)
        self.assertEqual(ssp.boes, [(29, 39), (22, 20, 18, 16, 14, 12, 10, 8, 6, 4)])
        print(ssp.boes)
        print('\ntest enum space and ignore enum axis')
        ssp = space_around_centre(space=sp, centre=p1, radius=5)
        self.assertEqual(ssp.boes, [(29, 39),
                                    (40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4)])
        print(sp.boes)

    def test_vector_axis_sizes(self):
        """测试 vector_axis_sizes 属性：标量轴为 1，数组轴为 np.prod(shape)。"""
        # int + float + enum -> [1, 1, 1]
        s = Space((1, 10), (3., 10.), (5, 6, 7, 8, 9))
        sizes = s.vector_axis_sizes
        self.assertEqual(sizes, [1, 1, 1], 'vector_axis_sizes for int/float/enum should be [1,1,1]')
        print('vector_axis_sizes int/float/enum:', sizes)

        # 含 array 轴
        s2 = Space((0., 1.), (0., 1.), par_types=['float_array[2]', 'float_array[2, 2]'])
        sizes2 = s2.vector_axis_sizes
        self.assertEqual(sizes2, [2, 4], 'vector_axis_sizes for array[2] and array[2,2] should be [2, 4]')
        print('vector_axis_sizes with array axes:', sizes2)

    def test_point_to_vector_and_vector_to_point(self):
        """测试 point_to_vector / vector_to_point 双向映射及 round-trip。"""
        # int, float, enum
        s = Space((1, 10), (3., 10.), (5, 6, 7, 8, 9))
        p = (5, 6.5, 7)
        self.assertIn(p, s)
        v = s.point_to_vector(p)
        self.assertIsInstance(v, np.ndarray)
        self.assertEqual(v.dtype, np.float64)
        self.assertEqual(v.shape, (3,))
        self.assertEqual(v[0], 5.0)
        self.assertEqual(v[1], 6.5)
        enum_list = list(s.boes[2])
        self.assertEqual(v[2], float(enum_list.index(7)))
        print('point_to_vector result:', v)

        p2 = s.vector_to_point(v)
        self.assertIsInstance(p2, tuple)
        self.assertEqual(len(p2), 3)
        self.assertEqual(p2[0], 5)
        self.assertEqual(p2[1], 6.5)
        self.assertEqual(p2[2], 7)
        self.assertIn(p2, s)
        print('vector_to_point round-trip:', p2)

        # 越界向量解码后应被 clip 到合法范围
        v_oob = np.array([100.0, -1.0, 0.0])
        p3 = s.vector_to_point(v_oob)
        self.assertEqual(p3[0], 10)
        self.assertEqual(p3[1], 3.0)
        self.assertEqual(p3[2], 5)
        self.assertIn(p3, s)
        print('vector_to_point with out-of-bound vector (clipped):', p3)

        # 含 array 轴的空间
        s_arr = Space((0., 1.), (0., 1.), par_types=['float_array[2]', 'float_array[2, 2]'])
        pt_arr = (np.array([0.2, 0.8]), np.array([[0.1, 0.2], [0.3, 0.4]]))
        self.assertIn(pt_arr, s_arr)
        v_arr = s_arr.point_to_vector(pt_arr)
        self.assertEqual(v_arr.size, 2 + 4)
        self.assertAlmostEqual(v_arr[0], 0.2)
        self.assertAlmostEqual(v_arr[1], 0.8)
        pt_arr2 = s_arr.vector_to_point(v_arr)
        self.assertIn(pt_arr2, s_arr)
        np.testing.assert_array_almost_equal(np.asarray(pt_arr2[0]), np.asarray(pt_arr[0]))
        np.testing.assert_array_almost_equal(np.asarray(pt_arr2[1]), np.asarray(pt_arr[1]))
        print('point_to_vector / vector_to_point with array axes: OK')

        # 点不在空间内应报错
        self.assertRaises(AssertionError, s.point_to_vector, (0, 0, 0))  # 0 不在 enum 中
        self.assertRaises(AssertionError, s.point_to_vector, (100, 5, 7))  # 100 超出 int 范围

    def test_neighbors(self):
        """测试 neighbors：仅指定轴变化，返回合法邻域点列表。"""
        s = Space((1, 10), (3., 10.), (5, 6, 7, 8, 9))
        p = (5, 6.5, 7)

        # float 维（axis_index=1）：应得到 ±step 两个候选（若与当前不同）
        nb1 = s.neighbors(p, 1, step=1.0)
        self.assertIsInstance(nb1, list)
        for q in nb1:
            self.assertIn(q, s)
            self.assertEqual(q[0], p[0])
            self.assertEqual(q[2], p[2])
            self.assertNotEqual(q[1], p[1])
        print('neighbors float axis:', nb1)

        # int 维（axis_index=0）
        nb0 = s.neighbors(p, 0)
        self.assertIsInstance(nb0, list)
        for q in nb0:
            self.assertIn(q, s)
            self.assertEqual(q[1], p[1])
            self.assertEqual(q[2], p[2])
        self.assertTrue(any(q[0] == 4 for q in nb0) or any(q[0] == 6 for q in nb0))
        print('neighbors int axis:', nb0)

        # enum 维（axis_index=2）
        nb2 = s.neighbors(p, 2, count=2)
        self.assertIsInstance(nb2, list)
        for q in nb2:
            self.assertIn(q, s)
            self.assertEqual(q[0], p[0])
            self.assertEqual(q[1], p[1])
            self.assertNotEqual(q[2], p[2])
            self.assertIn(q[2], (5, 6, 8, 9))
        print('neighbors enum axis:', nb2)

        # 边界点：int 在 1 时只有 +1 邻域
        p_edge = (1, 5.0, 5)
        nb_edge = s.neighbors(p_edge, 0)
        self.assertIn((2, 5.0, 5), nb_edge)
        print('neighbors at int boundary:', nb_edge)

        # float_array 维（axis_index=1）：邻域为同形状数组且仅该维与 point 不同
        s_farr = Space((0, 5), (0., 1.), par_types=['int', 'float_array[2]'])
        p_farr = (2, np.array([0.3, 0.7]))
        self.assertIn(p_farr, s_farr)
        nb_farr = s_farr.neighbors(p_farr, 1, count=3)
        self.assertIsInstance(nb_farr, list)
        for q in nb_farr:
            self.assertIn(q, s_farr)
            self.assertEqual(q[0], p_farr[0])
            self.assertEqual(np.asarray(q[1]).shape, (2,))
            self.assertFalse(np.array_equal(np.asarray(q[1]), np.asarray(p_farr[1])))
        print('neighbors float_array axis:', [tuple(np.asarray(x[1]) for x in nb_farr)])

        # int_array 维（axis_index=1）：同上，仅该维为整型数组且与 point 不同
        s_iarr = Space((0, 5), (0, 10), par_types=['int', 'int_array[2]'])
        p_iarr = (2, np.array([3, 7]))
        self.assertIn(p_iarr, s_iarr)
        nb_iarr = s_iarr.neighbors(p_iarr, 1, count=3)
        self.assertIsInstance(nb_iarr, list)
        for q in nb_iarr:
            self.assertIn(q, s_iarr)
            self.assertEqual(q[0], p_iarr[0])
            self.assertEqual(np.asarray(q[1]).shape, (2,))
            self.assertFalse(np.array_equal(np.asarray(q[1]), np.asarray(p_iarr[1])))
        print('neighbors int_array axis:', [tuple(np.asarray(x[1]) for x in nb_iarr)])

    def test_sample_subspace(self):
        """测试 sample_subspace：在中心邻域内采样 count 个点。"""
        s = Space((0, 10), (0., 10.))
        center = (5, 5.0)
        pts = s.sample_subspace(center, radius=2, count=5)
        self.assertIsInstance(pts, list)
        self.assertEqual(len(pts), 5)
        for q in pts:
            self.assertIn(q, s)
            self.assertGreaterEqual(q[0], 3)
            self.assertLessEqual(q[0], 7)
            self.assertGreaterEqual(q[1], 3.0)
            self.assertLessEqual(q[1], 7.0)
        print('sample_subspace int/float:', pts)

        # 含 enum：ignore_enums=True 时 enum 维保持全枚举
        s2 = Space((0, 5), (0., 5.), ('a', 'b', 'c'))
        center2 = (2, 2.5, 'b')
        pts2 = s2.sample_subspace(center2, radius=1, count=4, ignore_enums=True)
        self.assertEqual(len(pts2), 4)
        for q in pts2:
            self.assertIn(q, s2)
            self.assertIn(q[2], ('a', 'b', 'c'))
        print('sample_subspace with enum (ignore_enums=True):', pts2)

        # 中心不在空间内应报错
        self.assertRaises(AssertionError, s.sample_subspace, (100, 5.0), 1, 3)

        # float_array：子空间为每元素在 center±radius 内裁剪到轴边界
        s_fa = Space((0., 1.), (0., 1.), par_types=['float_array[2]', 'float_array[2, 2]'])
        center_fa = (np.array([0.3, 0.7]), np.array([[0.2, 0.3], [0.4, 0.5]]))
        self.assertIn(center_fa, s_fa)
        pts_fa = s_fa.sample_subspace(center_fa, radius=0.2, count=5)
        self.assertEqual(len(pts_fa), 5)
        for q in pts_fa:
            self.assertIn(q, s_fa)
            a1, a2 = np.asarray(q[0]), np.asarray(q[1])
            self.assertEqual(a1.shape, (2,))
            self.assertEqual(a2.shape, (2, 2))
            # 元素应在 [center - 0.2, center + 0.2] 裁剪到 [0, 1] 内
            self.assertTrue(np.all(a1 >= 0) and np.all(a1 <= 1))
            self.assertTrue(np.all(a2 >= 0) and np.all(a2 <= 1))
        print('sample_subspace float_array:', tuple(np.asarray(x[0]) for x in pts_fa))

        # int_array：标量 radius，子空间为每元素在 center±radius 内裁剪
        s_ia = Space((0, 10), (0, 10), par_types=['int_array[2]', 'int_array[2]'])
        center_ia = (np.array([4, 6]), np.array([2, 8]))
        self.assertIn(center_ia, s_ia)
        pts_ia = s_ia.sample_subspace(center_ia, radius=2, count=4)
        self.assertEqual(len(pts_ia), 4)
        for q in pts_ia:
            self.assertIn(q, s_ia)
            a1, a2 = np.asarray(q[0]), np.asarray(q[1])
            self.assertEqual(a1.shape, (2,))
            self.assertEqual(a2.shape, (2,))
            self.assertTrue(np.all(a1 >= 2) and np.all(a1 <= 8))
            self.assertTrue(np.all(a2 >= 0) and np.all(a2 <= 10))
        print('sample_subspace int_array:', tuple(np.asarray(x[0]) for x in pts_ia))

        # 按维 radius（list）：对 array 维使用对应半径
        radius_per_dim = [0.15, 0.25]  # 两维均为 array
        pts_fa2 = s_fa.sample_subspace(center_fa, radius=radius_per_dim, count=3)
        self.assertEqual(len(pts_fa2), 3)
        for q in pts_fa2:
            self.assertIn(q, s_fa)
        print('sample_subspace float_array with list radius:', len(pts_fa2))


class TestPool(unittest.TestCase):
    def setUp(self):
        self.p = ResultPool(5)
        self.items = ['first', 'second', (1, 2, 3), 'this', 24]
        self.perfs = [1, 2, 3, 4, 5]
        self.additional_result1 = ('abc', 12)
        self.additional_result2 = ([1, 2], -1)
        self.additional_result3 = (12, 5)

    def test_create(self):
        self.assertIsInstance(self.p, ResultPool)

    def test_operation(self):
        self.p.push(self.additional_result1[0], self.additional_result1[1])
        self.p.cut()
        self.assertEqual(self.p.item_count, 1)
        self.assertEqual(self.p.items, ['abc'])
        for item, perf in zip(self.items, self.perfs):
            self.p.push(item, perf)
        self.assertEqual(self.p.item_count, 6)
        self.assertEqual(self.p.items, ['abc', 'first', 'second', (1, 2, 3), 'this', 24])
        self.p.cut()
        self.assertEqual(self.p.items, ['second', (1, 2, 3), 'this', 24, 'abc'])
        self.assertEqual(self.p.perfs, [2, 3, 4, 5, 12])

        self.p.push(self.additional_result2[0], self.additional_result2[1])
        self.p.push(self.additional_result3[0], self.additional_result3[1])
        self.assertEqual(self.p.item_count, 7)
        self.p.cut(keep_largest=False)
        self.assertEqual(self.p.items, [[1, 2], 'second', (1, 2, 3), 'this', 24])
        self.assertEqual(self.p.perfs, [-1, 2, 3, 4, 5])


if __name__ == '__main__':
    unittest.main()
    