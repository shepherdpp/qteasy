# coding=utf-8
# ======================================
# File:     test_datatables.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-09-10
# Desc:
#   Unittest for all built-in data
# tables.
# ======================================

import unittest

from qteasy.datatables import TABLE_MASTERS
from qteasy.datatables import TABLE_SCHEMA


class TestDataTables(unittest.TestCase):
    def test_fullness(self):
        self.assertTrue(all(tbl[0] in TABLE_SCHEMA for tbl in TABLE_MASTERS.values()))
        self.assertEqual([tbl[0] for tbl in TABLE_MASTERS.values() if tbl[0] not in TABLE_SCHEMA],
                         [])


if __name__ == '__main__':
    unittest.main()