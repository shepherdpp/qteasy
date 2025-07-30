import unittest
import numpy as np

from qteasy.parameter import Parameter


class TestParameter(unittest.TestCase):
    def test_parameter(self):
        p = Parameter((0, 10),name='par1')
        self.assertEqual(p.name, 'par1')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.axis_boe, (0, 10))
        self.assertEqual(p.count, 11)
        self.assertEqual(p.size, 11)
        self.assertTrue(np.allclose(p.gen_values(1, 'int'), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
        self.assertRaises(ValueError, p.gen_values, 0.5, 'int')
        extracted = p.gen_values(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(0 <= item <= 10) for item in extracted]))
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
        self.assertEqual(p.axis_boe, (0.0, 1.0))
        self.assertEqual(p.count, np.inf)
        self.assertEqual(p.size, 1.0)
        self.assertEqual(p.upper_bound, 1.0)
        self.assertEqual(p.lower_bound, 0.0)
        self.assertEqual(p.ubound, 1.0)
        self.assertEqual(p.lbound, 0.0)
        print(p.gen_values(0.5, 'interval'))
        self.assertTrue(np.allclose(p.gen_values(0.5, 'interval'), [0.0, 0.5]))
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

        p = Parameter(('a', 'b'), name='par3')
        self.assertEqual(p.name, 'par3')
        self.assertEqual(p.par_type, 'enum')
        self.assertEqual(p.axis_boe, ('a', 'b'))
        self.assertEqual(p.count, 2)
        self.assertEqual(p.size, 2)
        self.assertEqual(p.ubound, 'b')
        self.assertEqual(p.lbound, 'a')
        self.assertEqual(p.upper_bound, 'b')
        self.assertEqual(p.lower_bound, 'a')
        self.assertEqual(list(p.gen_values(1, 'int')), ['a', 'b'])
        self.assertEqual(list(p.enum_values()), ['a', 'b'])
        self.assertTrue('a' in p)

        p = Parameter((1, 2, 3), name='par4')
        self.assertEqual(p.name, 'par4')
        self.assertEqual(p.par_type, 'enum')
        self.assertEqual(str(p), "Parameter((1, 2, 3), 'enum')")

        p = Parameter(3, name='par5')
        self.assertEqual(p.name, 'par5')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.axis_boe, (0, 3))

        p = Parameter(3.5, name='par6')
        self.assertEqual(p.name, 'par6')
        self.assertEqual(p.par_type, 'float')
        self.assertEqual(p.axis_boe, (0.0, 3.5))

        p = Parameter('a', name='par7')
        self.assertEqual(p.name, 'par7')
        self.assertEqual(p.par_type, 'enum')
        self.assertEqual(p.axis_boe, ('a', ))

        p = Parameter(5, typ='discr')
        self.assertEqual(p.name, '')
        self.assertEqual(p.par_type, 'int')

        self.assertRaises(ValueError, Parameter, 5, typ='wrong_type')

        p = Parameter((0, 10), name='par8', typ='int', value=5)
        self.assertEqual(p.name, 'par8')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.value, 5)

        p = Parameter((0.0, 8.0), name='par9', typ='int')
        self.assertEqual(p.name, 'par9')
        self.assertEqual(p.par_type, 'int')

        self.assertRaises(ValueError, Parameter, (0.0, 8.0), name='par10', typ='int', value=9.5)

        p = Parameter((10, -10), name='par10', typ='int')
        self.assertEqual(p.name, 'par10')
        self.assertEqual(p.par_type, 'int')
        self.assertEqual(p.axis_boe, (-10, 10))
        self.assertEqual(p.count, 21)
        self.assertEqual(p.size, 21)
        self.assertEqual(p.ubound, 10)
        values = p.gen_values(5, 'interval')
        self.assertTrue(np.allclose(values, [-10, -5, 0, 5, 10]))

        p = Parameter((-10.5, 10.5), typ='int')

    def test_gen_values(self):
        p = Parameter((0, 10), name='par11', typ='int')
        values = p.gen_values(2, 'interval')
        self.assertTrue(np.allclose(values, [0, 2, 4, 6, 8, 10]))
        values = p.gen_values(5, 'rand')
        self.assertEqual(len(values), 5)
        self.assertTrue(all([(0 <= item <= 10) for item in values]))

        p = Parameter((0.0, 10.0), name='par12', typ='float')
        values = p.gen_values(2.5, 'interval')
        self.assertTrue(np.allclose(values, [0.0, 2.5, 5.0, 7.5]))
        values = p.gen_values(5, 'rand')
        self.assertEqual(len(values), 5)
        self.assertTrue(all([(0.0 <= item <= 10.0) for item in values]))

        p = Parameter(('a', 'b', 'c', 'd', 'e', 'f'), name='par13', typ='enum')
        values = p.gen_values(2, how='int')
        self.assertEqual(values, ['a', 'c', 'e'])
        values = p.gen_values(3, how='rand')
        self.assertEqual(len(values), 3)
        self.assertTrue(all([item in ('a', 'b', 'c', 'd', 'e', 'f') for item in values]))


if __name__ == '__main__':
    unittest.main()