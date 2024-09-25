# coding=utf-8
# ======================================
# File:     test_datatypes.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-09-25
# Desc:
#   Unittest for all built-in data
# types.
# ======================================

import unittest

from qteasy.datatypes import DATA_TYPE_MAP
from qteasy.datatypes import DataType


class TestDataTypes(unittest.TestCase):
    def test_all_types(self):
        for k, v in DATA_TYPE_MAP.items():
            self.assertIsInstance(k, tuple)
            self.assertIsInstance(v, list)

            # create a new instance of the data type
            id, freq, asset_type = k
            dtype = DataType(
                    id=id,
                    freq=freq,
                    asset_type=asset_type,

            )


if __name__ == '__main__':
    unittest.main()