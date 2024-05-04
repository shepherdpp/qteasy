# coding=utf-8
# ======================================
# File:     test_freq.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-05-04
# Desc:
#   Unittest for DataFreq objects.
# ======================================

import unittest

from qteasy.frequency import DataFreq


class TestFreq(unittest.TestCase):

    def setUp(self):
        self.freq = DataFreq('D')

    def test_pattern_match(self):
        """ test all re patterns"""
        re_pattern = DataFreq.freq_string_validator
        self.assertTrue(re_pattern.match('D'))
        self.assertTrue(re_pattern.match('3D'))
        self.assertTrue(re_pattern.match('3W-Fri'))
        self.assertTrue(re_pattern.match('3W-Friday'))
        self.assertTrue(re_pattern.match('3W-1'))
        self.assertTrue(re_pattern.match('15min'))
        self.assertTrue(re_pattern.match('15MIN'))
        self.assertTrue(re_pattern.match('15T'))

    def test_class(self):
        freq = self.freq
        self.assertIsInstance(freq, DataFreq)

        freq = DataFreq(major='D')
        self.assertIsInstance(freq, DataFreq)

    def test_properties(self):
        freq = self.freq
        self.assertEqual(freq.freq_str, 'D')
        self.assertEqual(freq.multiple, 1)
        self.assertEqual(freq.major, 'D')
        self.assertEqual(freq.minor, None)

        freq = DataFreq('3D')
        self.assertEqual(freq.freq_str, '3D')
        self.assertEqual(freq.multiple, 3)
        self.assertEqual(freq.major, 'D')
        self.assertEqual(freq.minor, None)

        freq = DataFreq('3W-Fri')
        self.assertEqual(freq.freq_str, '3W-Fri')
        self.assertEqual(freq.multiple, 3)
        self.assertEqual(freq.major, 'W')
        self.assertEqual(freq.minor, 'FRI')

        freq = DataFreq('15min')
        self.assertEqual(freq.freq_str, '15min')
        self.assertEqual(freq.multiple, 15)
        self.assertEqual(freq.major, 'MIN')
        self.assertEqual(freq.minor, None)

        freq = DataFreq('15MIN')
        self.assertEqual(freq.freq_str, '15MIN')
        self.assertEqual(freq.multiple, 15)
        self.assertEqual(freq.major, 'MIN')
        self.assertEqual(freq.minor, None)

        freq = DataFreq('15T')
        self.assertEqual(freq.freq_str, '15T')
        self.assertEqual(freq.multiple, 15)
        self.assertEqual(freq.major, 'MIN')
        self.assertEqual(freq.minor, None)

    def test_generate_freq_str(self):
        freq = self.freq
        self.assertEqual(freq.generate_freq_str(1, 'D', None), 'D')
        self.assertEqual(freq.generate_freq_str(3, 'D', None), '3D')
        self.assertEqual(freq.generate_freq_str(3, 'W', 'Fri'), '3W-FRI')
        self.assertEqual(freq.generate_freq_str(15, 'MIN', None), '15MIN')
        self.assertEqual(freq.generate_freq_str(15, 'H', None), '15H')
        self.assertEqual(freq.generate_freq_str(15, 'T', None), '15MIN')
        self.assertEqual(freq.generate_freq_str(2, 'M', '1'), '2M-1')
        self.assertEqual(freq.generate_freq_str(1, 'M', '15'), 'M-15')


if __name__ == '__main__':
    unittest.main()