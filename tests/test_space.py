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

from qteasy.space import Space, Axis, space_around_centre, ResultPool


class TestSpace(unittest.TestCase):
    def test_creation(self):
        """
            test if creation of space object is fine
        """
        # first group of inputs, output Space with two discr axis from [0,10]
        print('testing space objects\n')
        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = ['int',
                      ['int', 'int']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            print(p)
            s = Space(*p)
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
            self.assertRaises(KeyError, Space, *p)

        pars_list = [[(0, 10), (0, 10)],
                     [[0, 10], [0, 10]]]

        types_list = [['int', 'enumerate']]

        input_pars = itertools.product(pars_list, types_list)
        for p in input_pars:
            s = Space(*p)
            b = s.boes
            t = s.types
            self.assertEqual(b, [(0, 10), (0, 10)], 'boes incorrect!')
            self.assertEqual(t, ['int', 'enum'], 'types incorrect')

        pars_list = [(0., 10), (0, 10)]
        s = Space(pars=pars_list, par_types=None)
        self.assertEqual(s.types, ['float', 'int'])
        self.assertEqual(s.dim, 2)
        self.assertEqual(s.size, (10.0, 11))
        self.assertEqual(s.shape, (np.inf, 11))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0., 10), (0, 10)])

        pars_list = [(0., 10), (0, 10)]
        s = Space(pars=pars_list, par_types='conti, enum')
        self.assertEqual(s.types, ['float', 'enum'])
        self.assertEqual(s.dim, 2)
        self.assertEqual(s.size, (10.0, 2))
        self.assertEqual(s.shape, (np.inf, 2))
        self.assertEqual(s.count, np.inf)
        self.assertEqual(s.boes, [(0., 10), (0, 10)])

        pars_list = [(1, 2), (2, 3), (3, 4)]
        s = Space(pars=pars_list)
        self.assertEqual(s.types, ['int', 'int', 'int'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (2, 2, 2))
        self.assertEqual(s.shape, (2, 2, 2))
        self.assertEqual(s.count, 8)
        self.assertEqual(s.boes, [(1, 2), (2, 3), (3, 4)])

        pars_list = [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
        s = Space(pars=pars_list)
        self.assertEqual(s.types, ['enum', 'enum', 'enum'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (3, 3, 3))
        self.assertEqual(s.shape, (3, 3, 3))
        self.assertEqual(s.count, 27)
        self.assertEqual(s.boes, [(1, 2, 3), (2, 3, 4), (3, 4, 5)])

        pars_list = [((1, 2, 3), (2, 3, 4), (3, 4, 5))]
        s = Space(pars=pars_list)
        self.assertEqual(s.types, ['enum'])
        self.assertEqual(s.dim, 1)
        self.assertEqual(s.size, (3,))
        self.assertEqual(s.shape, (3,))
        self.assertEqual(s.count, 3)

        pars_list = ((1, 2, 3), (2, 3, 4), (3, 4, 5))
        s = Space(pars=pars_list)
        self.assertEqual(s.types, ['enum', 'enum', 'enum'])
        self.assertEqual(s.dim, 3)
        self.assertEqual(s.size, (3, 3, 3))
        self.assertEqual(s.shape, (3, 3, 3))
        self.assertEqual(s.count, 27)
        self.assertEqual(s.boes, [(1, 2, 3), (2, 3, 4), (3, 4, 5)])

        print('testing space_around_centre')
        pars_list = [(0, 10), (0, 10)]
        s = Space(pars=pars_list, par_types=None)
        centre = (5, 5)
        distance = 2
        s2 = space_around_centre(s, centre, distance)
        self.assertEqual(s2.types, ['int', 'int'])
        self.assertEqual(s2.dim, 2)
        self.assertEqual(s2.size, (5, 5))
        self.assertEqual(s2.shape, (5, 5))
        self.assertEqual(s2.count, 25)
        self.assertEqual(s2.boes, [(3, 7), (3, 7)])

        pars_space = [(0., 10.), (0, 10), (0., 10.)]
        s = Space(pars=pars_space, par_types=None)
        centre = (5, 5, 5)
        distance = 2
        s2 = space_around_centre(s, centre, distance)
        self.assertEqual(s2.types, ['float', 'int', 'float'])
        self.assertEqual(s2.dim, 3)
        self.assertEqual(s2.size, (4.0, 5, 4.0))
        self.assertEqual(s2.shape, (np.inf, 5, np.inf))
        self.assertEqual(s2.count, np.inf)
        self.assertEqual(s2.boes, [(3, 7), (3, 7), (3, 7)])

    def test_extract(self):
        """

        :return:
        """
        pars_list = [(0, 10), (0, 10)]
        types_list = ['int', 'int']
        s = Space(pars=pars_list, par_types=types_list)
        extracted_int, count = s.extract(3, 'interval')
        extracted_int_list = list(extracted_int)
        print('extracted int\n', extracted_int_list)
        self.assertEqual(count, 16, 'extraction count wrong!')
        self.assertEqual(extracted_int_list, [(0, 0), (0, 3), (0, 6), (0, 9), (3, 0), (3, 3),
                                              (3, 6), (3, 9), (6, 0), (6, 3), (6, 6), (6, 9),
                                              (9, 0), (9, 3), (9, 6), (9, 9)],
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
        s = Space(pars=pars_list, par_types=None)
        extracted_int2, count = s.extract(3, 'interval')
        self.assertEqual(count, 16, 'extraction count wrong!')
        extracted_int_list2 = list(extracted_int2)
        self.assertEqual(extracted_int_list2, [(0, 0), (0, 3), (0, 6), (0, 9), (3, 0), (3, 3),
                                               (3, 6), (3, 9), (6, 0), (6, 3), (6, 6), (6, 9),
                                               (9, 0), (9, 3), (9, 6), (9, 9)],
                         'space extraction wrong!')
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
        s = Space(pars=pars_list, par_types='enum, enum')
        extracted_int3, count = s.extract(1, 'interval')
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

        pars_list = [((0, 10), (1, 'c'), ('a', 'b'), (1, 14))]
        s = Space(pars=pars_list, par_types='enum')
        extracted_int4, count = s.extract(1, 'interval')
        self.assertEqual(count, 4, 'extraction count wrong!')
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

        pars_list = [((0, 10), (1, 'c'), ('a', 'b'), (1, 14)), (1, 4)]
        s = Space(pars=pars_list, par_types='enum, discr')
        extracted_int5, count = s.extract(1, 'interval')
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
        pars_list = [(10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250)]
        s = Space(pars_list)
        ext, count = s.extract(64, 'interval')
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
            ext, count = subspace.extract(32)
            points = list(ext)
            self.assertGreaterEqual(count, 512)
            self.assertLessEqual(count, 4096)
            print(f'\n---------------------------------'
                  f'\nthe space created around point <{point}> is'
                  f'\n{subspace.boes}'
                  f'\nand extracted {count} points, the first 5 are:'
                  f'\n{points[:5]}')

    def test_axis_extract(self):
        # test axis object with conti type
        axis = Axis((0., 5))
        self.assertIsInstance(axis, Axis)
        self.assertEqual(axis.axis_type, 'float')
        self.assertEqual(axis.axis_boe, (0., 5.))
        self.assertEqual(axis.count, np.inf)
        self.assertEqual(axis.size, 5.0)
        self.assertTrue(np.allclose(axis.extract(1, 'int'), [0., 1., 2., 3., 4.]))
        self.assertTrue(np.allclose(axis.extract(0.5, 'int'), [0., 0.5, 1., 1.5, 2., 2.5, 3., 3.5, 4., 4.5]))
        extracted = axis.extract(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(0 <= item <= 5) for item in extracted]))

        # test axis object with discrete type
        axis = Axis((1, 5))
        self.assertIsInstance(axis, Axis)
        self.assertEqual(axis.axis_type, 'int')
        self.assertEqual(axis.axis_boe, (1, 5))
        self.assertEqual(axis.count, 5)
        self.assertEqual(axis.size, 5)
        self.assertTrue(np.allclose(axis.extract(1, 'int'), [1, 2, 3, 4, 5]))
        self.assertRaises(ValueError, axis.extract, 0.5, 'int')
        extracted = axis.extract(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(item in [1, 2, 3, 4, 5]) for item in extracted]))

        # test axis object with enumerate type
        axis = Axis((1, 5, 7, 10, 'A', 'F'))
        self.assertIsInstance(axis, Axis)
        self.assertEqual(axis.axis_type, 'enum')
        self.assertEqual(axis.axis_boe, (1, 5, 7, 10, 'A', 'F'))
        self.assertEqual(axis.count, 6)
        self.assertEqual(axis.size, 6)
        self.assertEqual(axis.extract(1, 'int'), [1, 5, 7, 10, 'A', 'F'])
        self.assertRaises(ValueError, axis.extract, 0.5, 'int')
        extracted = axis.extract(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(item in [1, 5, 7, 10, 'A', 'F']) for item in extracted]))

    def test_from_point(self):
        """测试从一个点生成一个space"""
        # 生成一个space，指定space中的一个点以及distance，生成一个sub-space
        pars_list = [(0., 10), (0, 10)]
        s = Space(pars=pars_list, par_types=None)
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
        s = Space(pars=[(10, 250), (10, 250), (10, 250), (10, 250), (10, 250), (10, 250)])
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
        s = Space(pars=[(10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250)])
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
        s = Space(pars=[(10., 250), (10., 250), (10., 250), (10., 250), (10., 250), (10., 250)])
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
        self.p.in_pool(self.additional_result1[0], self.additional_result1[1])
        self.p.cut()
        self.assertEqual(self.p.item_count, 1)
        self.assertEqual(self.p.items, ['abc'])
        for item, perf in zip(self.items, self.perfs):
            self.p.in_pool(item, perf)
        self.assertEqual(self.p.item_count, 6)
        self.assertEqual(self.p.items, ['abc', 'first', 'second', (1, 2, 3), 'this', 24])
        self.p.cut()
        self.assertEqual(self.p.items, ['second', (1, 2, 3), 'this', 24, 'abc'])
        self.assertEqual(self.p.perfs, [2, 3, 4, 5, 12])

        self.p.in_pool(self.additional_result2[0], self.additional_result2[1])
        self.p.in_pool(self.additional_result3[0], self.additional_result3[1])
        self.assertEqual(self.p.item_count, 7)
        self.p.cut(keep_largest=False)
        self.assertEqual(self.p.items, [[1, 2], 'second', (1, 2, 3), 'this', 24])
        self.assertEqual(self.p.perfs, [-1, 2, 3, 4, 5])


if __name__ == '__main__':
    unittest.main()