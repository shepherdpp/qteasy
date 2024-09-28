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

from qteasy.database import DataSource


class TestDataTypes(unittest.TestCase):

    def setUp(self):

        from qteasy import QT_CONFIG, QT_DATA_SOURCE

        print('preparing test data sources with configurations...')
        self.ds = DataSource(
                'db',
                host=QT_CONFIG['test_db_host'],
                port=QT_CONFIG['test_db_port'],
                user=QT_CONFIG['test_db_user'],
                password=QT_CONFIG['test_db_password'],
                db_name=QT_CONFIG['test_db_name']
        )

        self.ds = QT_DATA_SOURCE

    def test_all_types(self):
        ds = self.ds
        for k, v in DATA_TYPE_MAP.items():
            self.assertIsInstance(k, tuple)
            self.assertIsInstance(v, list)

            # create a new instance of the data type
            name, freq, asset_type = k
            desc = v[0]
            acq_type = v[1]
            kwargs = v[2]
            dtype = DataType(
                    name=name,
                    freq=freq,
                    asset_type=asset_type,
                    description=desc,
                    acquisition_type=acq_type,
                    **kwargs,
            )
            self.assertIsInstance(dtype, DataType)
            self.assertEqual(dtype.name, name)
            self.assertEqual(dtype.freq, freq)
            self.assertEqual(dtype.asset_type, asset_type)
            self.assertEqual(dtype.description, desc)
            self.assertEqual(dtype.acquisition_type, acq_type)

            print(f'getting data for {dtype} - {dtype.description}')

            if acq_type == 'basics':
                shares = ['000651.SZ']
            elif (acq_type == 'direct') and (asset_type == 'E'):
                shares = ['000651.SZ']
            elif (acq_type == 'direct') and (asset_type == 'IDX'):
                shares = ['000300.SH']
            else:
                shares = None

            data = ds.get_data(
                    dtype,
                    symbols=shares,
            )
            print(f'got {type(data)}: {data}')


if __name__ == '__main__':
    unittest.main()