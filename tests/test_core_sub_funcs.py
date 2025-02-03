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

import qteasy as qt
import pandas as pd
import numpy as np

from qteasy import QT_DATA_SOURCE

from qteasy.space import Space, space_around_centre


class TestCoreSubFuncs(unittest.TestCase):
    """Test all functions in core.py"""

    def setUp(self):
        pass

    def test_input_to_list(self):
        print('Testing input_to_list() function')
        input_str = 'first'
        self.assertEqual(qt.utilfuncs.input_to_list(input_str, 3), ['first', 'first', 'first'])
        self.assertEqual(qt.utilfuncs.input_to_list(input_str, 4), ['first', 'first', 'first', 'first'])
        self.assertEqual(qt.utilfuncs.input_to_list(input_str, 2, None), ['first', 'first'])
        input_list = ['first', 'second']
        self.assertEqual(qt.utilfuncs.input_to_list(input_list, 3), ['first', 'second', None])
        self.assertEqual(qt.utilfuncs.input_to_list(input_list, 4, 'padder'), ['first', 'second', 'padder', 'padder'])
        self.assertEqual(qt.utilfuncs.input_to_list(input_list, 1), ['first', 'second'])
        self.assertEqual(qt.utilfuncs.input_to_list(input_list, -5), ['first', 'second'])

    def test_point_in_space(self):
        sp = Space([(0., 10.), (0., 10.), (0., 10.)])
        p1 = (5.5, 3.2, 7)
        p2 = (-1, 3, 10)
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')
        self.assertFalse(p2 in sp)
        print(f'point {p2} is not in space {sp}')
        sp = Space([(0., 10.), (0., 10.), range(40, 3, -2)], 'conti, conti, enum')
        p1 = (5.5, 3.2, 8)
        self.assertTrue(p1 in sp)
        print(f'point {p1} is in space {sp}')

    def test_space_in_space(self):
        print('test if a space is in another space')
        sp = Space([(0., 10.), (0., 10.), (0., 10.)])
        sp2 = Space([(0., 10.), (0., 10.), (0., 10.)])
        self.assertTrue(sp2 in sp)
        self.assertTrue(sp in sp2)
        print(f'space {sp2} is in space {sp}\n'
              f'and space {sp} is in space {sp2}\n'
              f'they are equal to each other\n')
        sp2 = Space([(0, 5.), (2, 7.), (3., 9.)])
        self.assertTrue(sp2 in sp)
        self.assertFalse(sp in sp2)
        print(f'space {sp2} is in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'{sp2} is a sub space of {sp}\n')
        sp2 = Space([(0, 5), (2, 7), (3., 9)])
        self.assertFalse(sp2 in sp)
        self.assertFalse(sp in sp2)
        print(f'space {sp2} is not in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'they have different types of axes\n')
        sp = Space([(0., 10.), (0., 10.), range(40, 3, -2)])
        self.assertFalse(sp in sp2)
        self.assertFalse(sp2 in sp)
        print(f'space {sp2} is not in space {sp}\n'
              f'and space {sp} is not in space {sp2}\n'
              f'they have different types of axes\n')

    def test_space_around_centre(self):
        sp = Space([(0., 10.), (0., 10.), (0., 10.)])
        p1 = (5.5, 3.2, 7)
        ssp = space_around_centre(space=sp, centre=p1, radius=1.2)
        print(ssp.boes)
        print('\ntest multiple diameters:')
        self.assertEqual(ssp.boes, [(4.3, 6.7), (2.0, 4.4), (5.8, 8.2)])
        ssp = space_around_centre(space=sp, centre=p1, radius=[1, 2, 1])
        print(ssp.boes)
        self.assertEqual(ssp.boes, [(4.5, 6.5), (1.2000000000000002, 5.2), (6.0, 8.0)])
        print('\ntest points on edge:')
        p2 = (5.5, 3.2, 10)
        ssp = space_around_centre(space=sp, centre=p1, radius=3.9)
        print(ssp.boes)
        self.assertEqual(ssp.boes, [(1.6, 9.4), (0.0, 7.1), (3.1, 10.0)])
        print('\ntest enum spaces')
        sp = Space([(0, 100), range(40, 3, -2)], 'discr, enum')
        p1 = [34, 12]
        ssp = space_around_centre(space=sp, centre=p1, radius=5, ignore_enums=False)
        self.assertEqual(ssp.boes, [(29, 39), (22, 20, 18, 16, 14, 12, 10, 8, 6, 4)])
        print(ssp.boes)
        print('\ntest enum space and ignore enum axis')
        ssp = space_around_centre(space=sp, centre=p1, radius=5)
        self.assertEqual(ssp.boes, [(29, 39),
                                    (40, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4)])
        print(sp.boes)

    def test_filter_stocks(self):
        print(f'start test building stock pool function\n')
        ds = QT_DATA_SOURCE
        share_basics = ds.read_table_data('stock_basic')[['symbol', 'name', 'area', 'industry',
                                                          'market', 'list_date', 'exchange']]

        print(f'\nselect all stocks by area')
        stock_pool = qt.filter_stock_codes(area='上海')
        print(f'{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are "上海"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].eq('上海').all())

        print(f'\nselect all stocks by multiple areas')
        stock_pool = qt.filter_stock_codes(area='贵州,北京,天津')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are in list of ["贵州", "北京", "天津"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(['贵州',
                                                                                            '北京',
                                                                                            '天津']).all())

        print(f'\nselect all stocks by area and industry')
        stock_pool = qt.filter_stock_codes(area='四川', industry='银行, 金融')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock areas are "四川", and industry in ["银行", "金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].head()}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(['银行', '金融']).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(['四川']).all())

        print(f'\nselect all stocks by industry')
        stock_pool = qt.filter_stock_codes(industry='银行, 金融')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stocks industry in ["银行", "金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(['银行', '金融']).all())

        print(f'\nselect all stocks by market')
        stock_pool = qt.filter_stock_codes(market='主板')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock market is "主板"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['market'].isin(['主板']).all())

        print(f'\nselect all stocks by market and list date')
        stock_pool = qt.filter_stock_codes(date='2000-01-01', market='主板')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stock market is "主板", and list date after "2000-01-01"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['market'].isin(['主板']).all())
        date = pd.to_datetime('2000-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())

        print(f'\nselect all stocks by list date')
        stock_pool = qt.filter_stock_codes(date='1997-01-01')
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all list date after "1997-01-01"\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        date = pd.to_datetime('1997-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())

        print(f'\nselect all stocks by exchange')
        stock_pool = qt.filter_stock_codes(exchange='SSE')
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
        stock_pool = qt.filter_stock_codes(date='19980101',
                                           industry=industry_list,
                                           area=area_list)
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all exchanges are in\n{area_list} \nand \n{industry_list}'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        date = pd.to_datetime('1998-01-01').date()
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['list_date'].le(date).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(industry_list).all())
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['area'].isin(area_list).all())

        self.assertRaises(KeyError, qt.filter_stock_codes, industry=25)
        self.assertRaises(KeyError, qt.filter_stock_codes, share_name='000300.SH')
        self.assertRaises(KeyError, qt.filter_stock_codes, markets='SSE')

        print(f'\nselect all stocks by index, with start and end dates:\n'
              f'all the "000300.SH" composite after 20180101')
        stock_pool = qt.filter_stock_codes(date='20200101',
                                           index='000300.SH')
        self.assertTrue(len(stock_pool) > 0)
        print(f'\n{len(stock_pool)} shares selected, first 10 are: {stock_pool[0:10]}\n'
              f'more information of some fo the stocks\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')

        print(f'\nprint out targets that can not be matched and return fuzzy results')
        stock_pool = qt.filter_stock_codes(industry='银行业, 多元金融, 房地产',
                                           area='陕西省',
                                           market='主要')
        self.assertTrue(len(stock_pool) > 0)
        print(f'\n{len(stock_pool)} shares selected, first 5 are: {stock_pool[0:5]}\n'
              f'check if all stocks industry in ["多元金融"]\n'
              f'{share_basics[np.isin(share_basics.index, stock_pool)].sample(10)}')
        self.assertTrue(share_basics[np.isin(share_basics.index, stock_pool)]['industry'].isin(["多元金融"]).all())

    def test_get_basic_info(self):
        """ 测试获取证券基本信息"""
        print(f'getting basic info for "000300" - found IDX 000300.SH')
        qt.get_basic_info('000300')
        print('getting basic info for "000300.OF" - No result')
        qt.get_basic_info('000300.OF')
        print('getting basic infor for "004040" - found ')
        qt.get_basic_info('004040')
        qt.get_basic_info('沪镍')
        qt.get_basic_info('中国移动', verbose=True)

    def test_find_history_data(self):
        """ 测试查找打印历史数据信息"""
        qt.find_history_data('pe')
        qt.find_history_data('open')
        qt.find_history_data('市盈率')
        qt.find_history_data('市?率*')
        qt.find_history_data('市值')
        qt.find_history_data('net_profit')
        qt.find_history_data('净利润')

    def test_get_history_data(self):
        """ 测试get_history_data。大部份功能性测试在TestHistoryPanle.test_get_history_panel中完成
        这里只关注参数自动完善功能以及包含完整shares和htypes输入的功能"""
        print('test basic functions')
        print('read data with all parameters and output dataframe grouped by htypes')
        res = qt.get_history_data(shares='000002.SZ, 000001.SZ, 000300.SH',
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
        res = qt.get_history_data(shares='000002.SZ, 000001.SZ, 000300.SH',
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
        res = qt.get_history_data(htypes='open-000651.SZ, high-000006.SZ, low-000001.SZ')
        print(res)

        res = qt.get_history_data(htypes='open, close, vol',
                                  shares='000651.SZ, 513100.SH')
        print(res)

        print('test function with wrong parameters')
        print('wrong share code')
        res = qt.get_history_data(htypes='open, close, vol',
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


if __name__ == '__main__':
    unittest.main()