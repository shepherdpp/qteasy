# coding=utf-8
# ======================================
# File:     test_datasource_optional_deps_fallback.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-03-20
# Desc:
#   当可选依赖缺失时，验证 DataSource 的回退与目录可用性
# ======================================

import os
import unittest
import warnings
import builtins
from unittest import mock

from qteasy.database import DataSource


class TestDataSourceOptionalDepsFallback(unittest.TestCase):
    """测试 DataSource 在可选依赖缺失时的回退行为。"""

    def test_fallback_to_csv_when_tables_missing(self):
        print('\n[TestDataSourceOptionalDepsFallback] tables missing -> fallback to csv')
        file_loc = 'data_test_optional_deps_tables/'

        real_import = builtins.__import__

        def mocked_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'tables':
                raise ImportError('Mocked: tables missing')
            return real_import(name, globals, locals, fromlist, level)

        with mock.patch('builtins.__import__', side_effect=mocked_import):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                ds = DataSource(source_type='file', file_type='hdf', file_loc=file_loc)

        print('ds.file_type:', ds.file_type)
        print('ds.file_path:', getattr(ds, 'file_path', None))
        msgs = [str(wi.message).lower() for wi in w]
        print('warnings:', msgs)

        self.assertEqual(ds.file_type, 'csv')
        self.assertTrue(hasattr(ds, 'file_path'))
        self.assertTrue(os.path.isdir(ds.file_path))
        self.assertTrue(any(('tables' in m) and ('fallback' in m) for m in msgs))
        self.assertFalse(ds._file_exists('file_that_does_not_exist'))

    def test_fallback_to_csv_when_pyarrow_missing(self):
        print('\n[TestDataSourceOptionalDepsFallback] pyarrow missing -> fallback to csv')
        file_loc = 'data_test_optional_deps_pyarrow/'

        real_import = builtins.__import__

        def mocked_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'pyarrow':
                raise ImportError('Mocked: pyarrow missing')
            return real_import(name, globals, locals, fromlist, level)

        with mock.patch('builtins.__import__', side_effect=mocked_import):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                ds = DataSource(source_type='file', file_type='fth', file_loc=file_loc)

        print('ds.file_type:', ds.file_type)
        print('ds.file_path:', getattr(ds, 'file_path', None))
        msgs = [str(wi.message).lower() for wi in w]
        print('warnings:', msgs)

        self.assertEqual(ds.file_type, 'csv')
        self.assertTrue(hasattr(ds, 'file_path'))
        self.assertTrue(os.path.isdir(ds.file_path))
        self.assertTrue(any(('pyarrow' in m) and ('fallback' in m) for m in msgs))
        self.assertFalse(ds._file_exists('file_that_does_not_exist'))


if __name__ == '__main__':
    unittest.main()

