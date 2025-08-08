import unittest
import numpy as np

from qteasy.parameter import Parameter


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


if __name__ == '__main__':
    unittest.main()