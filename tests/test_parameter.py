import unittest
import numpy as np

from qteasy.parameter import Parameter


class TestParameter(unittest.TestCase):
    def test_parameter(self):
        p = Parameter((0, 10))
        self.assertEqual(p.axis_type, 'int')
        self.assertEqual(p.axis_boe, (0, 10))
        self.assertEqual(p.count, 11)
        self.assertEqual(p.size, 11)
        self.assertTrue(np.allclose(p.gen_value(1, 'int'), [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]))
        self.assertRaises(ValueError, p.gen_value, 0.5, 'int')
        extracted = p.gen_value(8, 'rand')
        self.assertEqual(len(extracted), 8)
        self.assertTrue(all([(0 <= item <= 10) for item in extracted]))

        p = Parameter((0.0, 1.0))


if __name__ == '__main__':
    unittest.main()