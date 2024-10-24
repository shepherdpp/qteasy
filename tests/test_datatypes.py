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

import pandas as pd

from qteasy.database import DataSource
from qteasy.utilfuncs import progress_bar

from qteasy.datatypes import (
    DATA_TYPE_MAP,
    DataType,
)


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
        total = len(DATA_TYPE_MAP)
        acquired = 0
        empty_count = 0
        empty_types = []
        empty_type_descs = []
        empty_type_acq_types = []
        all_tables = ds.all_tables
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

            table_name = dtype.kwargs['table_name']

            shares = None
            starts = '2019-09-01'
            ends = '2020-09-12'

            type_with_shares = ['direct', 'basics']
            type_with_events = ['event_status', 'event_signal', 'event_multi_stat']
            if (acq_type in type_with_shares) and (asset_type == 'E'):
                shares = ['000651.SZ', '000001.SZ','002936.SZ', '603810.SH']
            elif (acq_type in type_with_shares) and (asset_type == 'IDX'):
                shares = ['000300.SH', '000001.SH']
            elif (acq_type in type_with_shares) and (asset_type == 'FD'):
                shares = ['515630.SH']
            elif (acq_type in type_with_shares) and (asset_type == 'FT'):
                shares = ['A0001.DCE', 'A.DCE', 'CU2310.SHF']
            elif (acq_type in type_with_shares) and (asset_type == 'OPT'):
                shares = ['10000001.SH', '10001909.SH', '10001910.SH', '10001911.SH', '10007976.SH']
            elif (acq_type in type_with_events) and (asset_type == 'E'):
                shares = ['000007.SZ', '000017.SZ', '000003.SZ', '600019.SH', '6000009.SH']
                starts = '2018-01-01'
                ends = '2020-05-01'
                # for special tables:
                if table_name == 'stock_suspend':
                    starts = '2020-03-10'
                    ends = '2020-03-13'
                elif table_name == 'top_inst':
                    starts = '2021-05-21'
                    ends = '2021-05-25'
            elif (acq_type in type_with_events) and (asset_type == 'FD'):
                shares = ['000152.OF', '960032.OF', '000152.OF']
                starts = '2018-01-01'
                ends = '2020-05-01'

            if (asset_type in 'E') and (freq[-3:] == 'min'):
                starts = '2022-04-01'
                ends = '2022-04-15'
            elif (asset_type == 'FT') and (freq[-3:] == 'min'):
                starts = '2023-08-25'
                ends = '2023-08-27'
            elif (asset_type == 'OPT') and (freq[-3:] == 'min'):
                starts = '2024-09-27'
                ends = '2024-09-28'
            elif (asset_type == 'FD') and (freq == 'h'):
                starts = '2021-09-20'
                ends = '2021-09-30'
            elif freq[-3:] == 'min':
                starts = '2022-04-01'
                ends = '2022-04-15'

            data = ds.get_data(
                    dtype,
                    symbols=shares,
                    starts=starts,
                    ends=ends,
            )

            acquired += 1
            progress_bar(acquired, total, f'{dtype} - {dtype.description}')

            try:
                all_tables.remove(table_name)
            except ValueError:
                pass

            if data.empty:
                empty_count += 1
                empty_types.append(k)
                empty_type_descs.append(desc)
                empty_type_acq_types.append(acq_type)
                # print(f'\nempty data for {dtype} - {dtype.description}')
                # print(f'got {type(data)}: \n{data}')

        print(f'\n{empty_count} out of {total} empty data types:')
        emptys = pd.DataFrame({
            'type': empty_types,
            'description': empty_type_descs,
            'acquisition_type': empty_type_acq_types
        })
        print(emptys.to_string())
        print('\n')
        print(f'{len(all_tables)} tables are not covered, those are:')
        for table in all_tables:
            print(ds.get_table_info(table))


if __name__ == '__main__':
    unittest.main()