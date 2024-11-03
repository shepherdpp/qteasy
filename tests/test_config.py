# coding=utf-8
# ======================================
# File:     test_config.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Unittest for all qteasy
#   configuration related functions.
# ======================================
import unittest

import qteasy as qt

from qteasy import QT_CONFIG

from qteasy._arg_validators import _parse_string_kwargs, _valid_qt_kwargs
from qteasy.configure import _parse_start_up_config_lines


class TestConfig(unittest.TestCase):
    """测试Config对象以及QT_CONFIG变量的设置和获取值"""

    def test_init(self):
        pass

    def test_save_load_reset_config(self):
        """保存读取重置configuration"""
        conf = {'mode':                2,
                'invest_cash_amounts': [200000]}
        qt.configure(**conf)
        qt.save_config(config=QT_CONFIG, file_name='saved3.cfg')
        qt.load_config(config=QT_CONFIG, file_name='saved3.cfg')
        print(QT_CONFIG)
        self.assertEqual(QT_CONFIG.mode, 2)
        self.assertEqual(QT_CONFIG.invest_cash_amounts, [200000])
        qt.reset_config()
        print(QT_CONFIG)
        self.assertEqual(QT_CONFIG.mode, 1)
        self.assertEqual(QT_CONFIG.invest_cash_amounts, [100000])

        # save and load config but don't overwrite QT_CONFIG
        conf = {'mode':                0,
                'invest_cash_amounts': [50000]}
        qt.save_config(config=conf, file_name='saved4.cfg')
        loaded_config = qt.load_config(file_name='saved4.cfg')
        print(loaded_config)
        self.assertEqual(loaded_config['mode'], 0)
        self.assertEqual(loaded_config['invest_cash_amounts'], [50000])
        self.assertEqual(QT_CONFIG.mode, 1)
        self.assertEqual(QT_CONFIG.invest_cash_amounts, [100000])

    def test_config(self):
        """测试设置不同的配置值，包括测试不合法的配置值以及不存在的配置值"""
        # test legal parameter configurations in QT_CONFIG
        qt.reset_config()
        self.assertEqual(QT_CONFIG.mode, 1)
        self.assertEqual(QT_CONFIG.opti_type, 'single')
        self.assertEqual(QT_CONFIG.cash_delivery_period, 0)
        self.assertEqual(QT_CONFIG.backtest_price_adj, 'none')
        self.assertEqual(QT_CONFIG.invest_start, '20160405')
        self.assertEqual(QT_CONFIG.cost_rate_buy, 0.0003)
        self.assertEqual(QT_CONFIG.benchmark_asset, '000300.SH')

        qt.configure(
                mode=2,
                opti_type='multiple',
                cash_delivery_period=1,
                backtest_price_adj='b',
                invest_start='20191010',
                cost_rate_buy=0.005,
                benchmark_asset='000001.SH'
        )
        self.assertEqual(QT_CONFIG.mode, 2)
        self.assertEqual(QT_CONFIG.opti_type, 'multiple')
        self.assertEqual(QT_CONFIG.cash_delivery_period, 1)
        self.assertEqual(QT_CONFIG.backtest_price_adj, 'b')
        self.assertEqual(QT_CONFIG.invest_start, '20191010')
        self.assertEqual(QT_CONFIG.cost_rate_buy, 0.005)
        self.assertEqual(QT_CONFIG.benchmark_asset, '000001.SH')
        # test legal parameter configurations in other Config objects

        # test illegal parameter configurations
        # illegal values
        self.assertRaises(Exception, qt.configure, mode=5)
        self.assertRaises(Exception, qt.configure, opti_type='mul')
        self.assertRaises(Exception, qt.configure, cash_delivery_period='abc')
        self.assertRaises(Exception, qt.configure, backtest_price_adj='wrong')
        self.assertRaises(Exception, qt.configure, invest_start=None)
        self.assertRaises(Exception, qt.configure, benchmark_asset=15)
        # parameters that do not exist
        self.assertRaises(Exception, qt.configure, wrong_parameter=3)
        self.assertRaises(Exception, qt.configure, not_existed=3)
        # user defined parameters
        qt.configure(
                only_built_in_keys=False,
                self_defined_par1=2,
                self_defined_par2='user_defined_value'
        )
        self.assertEqual(QT_CONFIG.self_defined_par1, 2)
        self.assertEqual(QT_CONFIG.self_defined_par2, 'user_defined_value')

    def test_pars_string_to_type(self):
        _parse_string_kwargs('000300', 'asset_pool', _valid_qt_kwargs())

    def test_parse_start_up_config_lines(self):
        """ test the function that parses start up configuration lines """
        config_line = [
            'mode = 2',
            'opti_type = None',
            'cash_delivery_period = 1',
            'local_db_name = True',
            'local_db_host = 3306',
            'local_db_user = root',
            'local_db_password = \'123456\'',
        ]
        configs = _parse_start_up_config_lines(config_lines=config_line)
        print(configs)
        self.assertEqual(configs['mode'], 2)
        self.assertEqual(configs['opti_type'], None)
        self.assertEqual(configs['cash_delivery_period'], 1)
        self.assertEqual(configs['local_db_name'], True)
        self.assertEqual(configs['local_db_host'], 3306)
        self.assertEqual(configs['local_db_user'], 'root')
        self.assertEqual(configs['local_db_password'], '123456')

        config_line = [
            'mode = 2',
            'opti_type = multiple',
            'cash_delivery_period = "1"',
            'local_db_name = test_db',
            "local_db_host = '3306'",
            'local_db_user = 345.6',
            'local_db_password = "123456"',
        ]
        configs = _parse_start_up_config_lines(config_lines=config_line)
        print(configs)
        self.assertEqual(configs['mode'], 2)
        self.assertEqual(configs['opti_type'], 'multiple')
        self.assertEqual(configs['cash_delivery_period'], "1")
        self.assertEqual(configs['local_db_name'], 'test_db')
        self.assertEqual(configs['local_db_host'], '3306')
        self.assertEqual(configs['local_db_user'], 345.6)
        self.assertEqual(configs['local_db_password'], '123456')

        config_line = [
            'mode = 2',
            'opti_type = false',
            'cash_delivery_period = 1',
            'local_db_name = False',
            'local_db_host = "3306',
            'local_db_user = 12345678',
            'local_db_password = "12345.6"',
        ]
        configs = _parse_start_up_config_lines(config_lines=config_line)
        print(configs)
        self.assertEqual(configs['mode'], 2)
        self.assertEqual(configs['opti_type'], 'false')
        self.assertEqual(configs['cash_delivery_period'], 1)
        self.assertEqual(configs['local_db_name'], False)
        self.assertEqual(configs['local_db_host'], '"3306')
        self.assertEqual(configs['local_db_user'], 12345678)
        self.assertEqual(configs['local_db_password'], '12345.6')

        config_line = [
            'mode = 2',
            'opti_type = multiple',
            'cash_delivery_period = 1',
            'local_db_name = test_db',
            'local_db_host = 3306',
            'local_db_user = root',
            'local_db_password = 12345a6',
        ]
        configs = _parse_start_up_config_lines(config_lines=config_line)
        print(configs)
        self.assertEqual(configs['mode'], 2)
        self.assertEqual(configs['opti_type'], 'multiple')
        self.assertEqual(configs['cash_delivery_period'], 1)
        self.assertEqual(configs['local_db_name'], 'test_db')
        self.assertEqual(configs['local_db_host'], 3306)
        self.assertEqual(configs['local_db_user'], 'root')
        self.assertEqual(configs['local_db_password'], '12345a6')


if __name__ == '__main__':
    unittest.main()