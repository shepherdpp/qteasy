# coding=utf-8
# ======================================
# File:     test_core_sub_funcs.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all qteasy core
#   sub-functions.
# ======================================
import unittest

import pandas as pd
import numpy as np

from qteasy import QT_DATA_SOURCE


class TestCoreSubFuncs(unittest.TestCase):
    """Test all functions in core.py"""

    def test_filter_stocks(self):

        from qteasy import filter_stock_codes
        print(f'start test building stock pool function\n')
        ds = QT_DATA_SOURCE
        share_basics = ds.read_table_data('stock_basic')[['symbol', 'name', 'area', 'industry',
                                                          'market', 'list_date', 'exchange']]

        print(f'\nselect all stocks by area')
        stock_pool = filter_stock_codes(area='上海')
        print(f'{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are "上海"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].eq('上海').all())

        print(f'\nselect all stocks by multiple areas')
        stock_pool = filter_stock_codes(area='贵州,北京,天津')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are in list of ["贵州", "北京", "天津"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(['贵州',
                                                                                            '北京',
                                                                                            '天津']).all())

        print(f'\nselect all stocks by area and industry')
        stock_pool = filter_stock_codes(area='四川', industry='银行, 金融')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are "四川", and industry in ["银行", "金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(['银行', '金融']).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(['四川']).all())

        print(f'\nselect all stocks by industry')
        stock_pool = filter_stock_codes(industry='银行, 金融')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stocks industry in ["银行", "金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(['银行', '金融']).all())

        print(f'\nselect all stocks by market')
        stock_pool = filter_stock_codes(market='主板')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock market is "主板"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['market'].isin(['主板']).all())

        print(f'\nselect all stocks by market and list date')
        stock_pool = filter_stock_codes(date='2000-01-01', market='主板')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock market is "主板", and list date after "2000-01-01"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['market'].isin(['主板']).all())
        date = pd.to_datetime('2000-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())

        print(f'\nselect all stocks by list date')
        stock_pool = filter_stock_codes(date='1997-01-01')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all list date after "1997-01-01"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        date = pd.to_datetime('1997-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())

        print(f'\nselect all stocks by exchange')
        stock_pool = filter_stock_codes(exchange='SSE')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all exchanges are in "SSE"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['exchange'].eq('SSE').all())

        print(f'\nselect all stocks by industry, area and list date')
        industry_list = ['银行', '全国地产', '互联网', '环境保护', '区域地产',
                         '酒店餐饮', '运输设备', '综合类', '建筑工程', '玻璃',
                         '家用电器', '文教休闲', '其他商业', '元器件', 'IT设备',
                         '其他建材', '汽车服务', '火力发电', '医药商业', '汽车配件',
                         '广告包装', '轻工机械', '新型电力', '多元金融', '饲料']
        area_list = ['深圳', '北京', '吉林', '江苏', '辽宁', '广东',
                     '安徽', '四川', '浙江', '湖南', '河北', '新疆',
                     '山东', '河南', '山西', '江西', '青海', '湖北',
                     '内蒙', '海南', '重庆', '陕西', '福建', '广西',
                     '上海']
        stock_pool = filter_stock_codes(date='19980101',
                                           industry=industry_list,
                                           area=area_list)
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all exchanges are in\n{area_list} \nand \n{industry_list}'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        date = pd.to_datetime('1998-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(industry_list).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(area_list).all())

        self.assertRaises(KeyError, filter_stock_codes, industry=25)
        self.assertRaises(KeyError, filter_stock_codes, share_name='000300.SH')
        self.assertRaises(KeyError, filter_stock_codes, markets='SSE')

        print(f'\nselect all stocks by index, with start and end dates:\n'
              f'all the "000300.SH" composite after 20180101')
        stock_pool = filter_stock_codes(date='20200101',
                                           index='000300.SH')
        self.assertTrue(len(stock_pool) > 0)
        print(f'\n{len(stock_pool)} shares selected, first 10 are: {stock_pool[0:10]}\n'
              f'more information of some fo the stocks\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')

        print(f'\nprint out targets that can not be matched and return fuzzy results')
        stock_pool = filter_stock_codes(industry='银行业, 多元金融, 房地产',
                                           area='陕西省',
                                           market='主要')
        self.assertTrue(len(stock_pool) > 0)
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stocks industry in ["多元金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(["多元金融"]).all())

    def test_get_basic_info(self):
        """ 测试获取证券基本信息"""
        from qteasy import get_basic_info
        print(f'getting basic info for "000300" - found IDX 000300.SH')
        get_basic_info('000300')
        print('getting basic info for "000300.OF" - No result')
        get_basic_info('000300.OF')
        print('getting basic infor for "004040" - found ')
        get_basic_info('004040')
        get_basic_info('沪镍')
        get_basic_info('中国移动', verbose=True)

    def test_find_history_data(self):
        """ 测试查找打印历史数据信息"""
        from qteasy import find_history_data
        find_history_data('pe')
        find_history_data('open')
        find_history_data('市盈率')
        find_history_data('市?率*')
        find_history_data('市值')
        find_history_data('net_profit')
        find_history_data('净利润')

    def test_get_history_data(self):
        """ 测试get_history_data。大部份功能性测试在TestHistoryPanle.test_get_history_panel中完成
        这里只关注参数自动完善功能以及包含完整shares和htypes输入的功能"""
        from qteasy import get_history_data
        print('test basic functions')
        print('read data with all parameters and output dataframe grouped by htypes')
        res = get_history_data(shares='000002.SZ, 000001.SZ, 000300.SH',
                                  htypes='open, high, low, close',
                                  start='20210101',
                                  end='20210115',
                                  freq='d',
                                  asset_type='E',
                                  adj='f',
                                  group_by='htypes')
        self.assertIsInstance(res, dict)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in res.values()))
        self.assertEqual(list(res.keys()), ['open|f', 'high|f', 'low|f', 'close|f'])
        first_df = res['open|f']
        first_index = first_df.index
        first_columns = first_df.columns
        for df in res.values():
            self.assertEqual(list(first_index), list(df.index))
            self.assertEqual(list(first_columns), list(df.columns))

        print('read data with all parameters and output dataframe grouped by shares')
        res = get_history_data(shares='000002.SZ, 000001.SZ, 000300.SH',
                                  htypes='open, high, low, close',
                                  start='20210101',
                                  end='20210115',
                                  freq='d',
                                  asset_type='E',
                                  adj='f',
                                  group_by='shares')
        self.assertIsInstance(res, dict)
        self.assertTrue(all(isinstance(item, pd.DataFrame) for item in res.values()))
        self.assertEqual(list(res.keys()), ['000002.SZ', '000001.SZ', '000300.SH'])
        first_df = res['000002.SZ']
        first_index = first_df.index
        first_columns = first_df.columns
        for df in res.values():
            self.assertEqual(list(first_index), list(df.index))
            self.assertEqual(list(first_columns), list(df.columns))

        print('test function with missing parameters')
        res = get_history_data(htypes='open-000651.SZ, high-000006.SZ, low-000001.SZ')
        print(res)

        res = get_history_data(htypes='open, close, vol',
                                  shares='000651.SZ, 513100.SH')
        print(res)

        print('test function with wrong parameters')
        print('wrong share code')
        res = get_history_data(htypes='open, close, vol',
                                  shares='missing_code, 513100.SH')
        print(res)
        print('wrong date')
        self.assertRaises(ValueError,
                          qt.get_history_data,
                          htypes='open, close, vol',
                          shares='missing_code, 513100.SH',
                          start='20220101',
                          end='20210101'
                          )
        self.assertRaises(Exception,
                          qt.get_history_data,
                          htypes='open, close, vol',
                          shares='missing_code, 513100.SH',
                          start='wrong_date',
                          end='20210101'
                          )
        print('wrong freq')
        self.assertRaises(Exception,
                          qt.get_history_data,
                          htypes='open, close, vol',
                          shares='missing_code, 513100.SH',
                          freq='wrong_freq'
                          )
        print('wrong asset_type')
        self.assertRaises(Exception,
                          qt.get_history_data,
                          htypes='open, close, vol',
                          shares='missing_code, 513100.SH',
                          asset_type='wrong_type'
                          )
        print('wrong adj')
        self.assertRaises(Exception,
                          qt.get_history_data,
                          htypes='open, close, vol',
                          shares='missing_code, 513100.SH',
                          adj='wrong_adj'
                          )

    def test_get_backtest_data_package(self):
        """ 测试获取回测数据包"""
        print('test get backtest data package')

    def test_get_backtest_cashplan(self):
        """ 测试获取回测资金计划"""
        print('test get backtest cashplan')


if __name__ == '__main__':
    unittest.main()