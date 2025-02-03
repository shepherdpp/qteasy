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

from qteasy.datatables import (
    TABLE_MASTERS,
    TABLE_SCHEMA,
    get_tables_by_name_or_usage,
    get_table_map,
    get_table_master,
)


class TestDataTables(unittest.TestCase):
    def test_fullness(self):
        self.assertTrue(all(tbl[0] in TABLE_SCHEMA for tbl in TABLE_MASTERS.values()))
        self.assertEqual([tbl[0] for tbl in TABLE_MASTERS.values() if tbl[0] not in TABLE_SCHEMA],
                         [])

    def test_parse_table_names(self):
        """ test function get_tables_by_name_or_usage"""
        tables = ['all']
        print(f'testing parsing table names {tables}')
        res = get_tables_by_name_or_usage(tables, include_sys_tables=True)
        print(f'fetching all tables: \n{res}')
        print('tables under expected', [table for table in TABLE_MASTERS.keys() if table not in res])
        print('tables more than expected', [table for table in res if table not in TABLE_MASTERS.keys()])
        self.assertTrue(all(table in res for table in TABLE_MASTERS.keys()))
        self.assertTrue(all(table in TABLE_MASTERS.keys() for table in res))

        tables = ['all']
        print(f'testing parsing table names {tables}')
        table_master = get_table_master()
        res = get_tables_by_name_or_usage(tables, include_sys_tables=False)
        all_tables = table_master.loc[table_master.table_usage != 'sys'].index.to_list()
        print(f'fetching all tables: \n{res}')
        print('tables under expected', [table for table in all_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in all_tables])
        self.assertTrue(all(table in res for table in all_tables))
        self.assertTrue(all(table in all_tables for table in res))

        tables = ['stock_basic', 'stock_daily', 'index_daily']
        res = get_tables_by_name_or_usage(tables=tables)
        print(f'fetching tables: stock_basic, stock_daily, index_daily: \n{res}')
        expected_tables = ['stock_basic', 'stock_daily', 'index_daily']
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['basics']
        res = get_tables_by_name_or_usage(tables=tables)
        print(f'fetching tables: basics: \n{res}')
        expected_tables = ['stock_basic', 'index_basic', 'fund_basic', 'future_basic', 'opt_basic',
                           'ths_index_basic',
                           'stock_company', 'new_share', 'sw_industry_basic']
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['events']
        res = get_tables_by_name_or_usage(tables=tables)
        print(f'fetching tables: events: \n{res}')
        expected_tables = ['stock_suspend', 'dividend', 'hs_top10_stock', 'block_trade', 'stock_holder_trade',
                           'stock_names', 'margin_detail', 'hk_top10_stock', 'stk_managers',
                           'top_list', 'fund_manager', 'top_inst']
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['mins']
        res = get_tables_by_name_or_usage(tables=tables)
        print(f'fetching tables: mins: \n{res}')
        expected_tables = ['fund_15min', 'future_15min', 'fund_1min', 'options_1min',
                           'stock_15min', 'index_5min', 'stock_hourly', 'options_5min',
                           'stock_30min',
                           'options_hourly', 'future_1min', 'index_15min', 'fund_30min',
                           'future_hourly',
                           'fund_hourly', 'future_30min', 'options_15min', 'options_30min', 'stock_5min',
                           'index_hourly', 'future_5min', 'stock_1min', 'index_30min', 'index_1min', 'fund_5min']
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['mins', 'events']
        freq = ['h']
        expected_tables = ['fund_hourly', 'future_hourly', 'options_hourly', 'stock_hourly', 'index_hourly',
                           'future_30min', 'index_30min', 'fund_15min', 'options_1min', 'options_5min', 'future_1min',
                           'index_5min', 'top_inst', 'stock_30min', 'stk_managers', 'options_30min', 'index_15min',
                           'options_15min', 'stock_holder_trade', 'stock_suspend', 'stock_5min', 'hk_top10_stock',
                           'top_list', 'stock_names', 'block_trade', 'fund_5min', 'future_15min', 'fund_30min',
                           'future_5min', 'stock_15min', 'hs_top10_stock', 'dividend', 'stock_1min', 'fund_1min',
                           'fund_manager', 'index_1min', 'margin_detail']
        res = get_tables_by_name_or_usage(tables=tables)
        print(f'fetching tables: mins, events: \n{res}')
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

        tables = ['stock_basic', 'stock_daily', 'index_daily']
        freq = ['d']
        dtypes = ['close']
        expected_tables = ['stock_basic', 'stock_daily', 'index_daily']
        res = get_tables_by_name_or_usage(tables=tables)
        print(f'fetching tables: stock_basic, stock_daily, index_daily: \n{res}')
        print('tables under expected', [table for table in expected_tables if table not in res])
        print('tables more than expected', [table for table in res if table not in expected_tables])
        self.assertTrue(all(table in res for table in expected_tables))
        self.assertTrue(all(table in expected_tables for table in res))

    def test_get_table_map(self):
        table_map = get_table_map()
        print(f'table map: \n{table_map}')
        print(f'tables only in TABLE_MASTERS: {[table for table in TABLE_MASTERS.keys() if table not in table_map.index]}')
        print(f'tables only in table_map: {[table for table in table_map.index if table not in TABLE_MASTERS.keys()]}')
        self.assertTrue(all(table in table_map.index for table in TABLE_MASTERS.keys()))
        self.assertTrue(all(table in TABLE_MASTERS.keys() for table in table_map.index))

    def test_get_table_master(self):
        table_master = get_table_master()
        print(f'table master: \n{table_master}')
        print(f'tables only in TABLE_MASTERS: {[table for table in TABLE_MASTERS.keys() if table not in table_master.index]}')
        print(f'tables only in table_master: {[table for table in table_master.index if table not in TABLE_MASTERS.keys()]}')
        self.assertTrue(all(table in table_master.index for table in TABLE_MASTERS.keys()))
        self.assertTrue(all(table in TABLE_MASTERS.keys() for table in table_master.index))
        # assert all tables' schema has been defined in TABLE_SCHEMA
        self.assertTrue(all(table_master.loc[table, 'schema'] in TABLE_SCHEMA for table in table_master.index))


if __name__ == '__main__':
    unittest.main()