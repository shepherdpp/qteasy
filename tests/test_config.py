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


class TestConfig(unittest.TestCase):
    """测试Config对象以及QT_CONFIG变量的设置和获取值"""

    def test_init(self):
        pass

    def test_save_load_reset_config(self):
        """保存读取重置configuration"""
        conf = {'mode':                2,
                'invest_cash_amounts': [200000]}
        qt.configure(**conf)
        qt.save_config(QT_CONFIG, 'saved3.cfg')
        qt.load_config(QT_CONFIG, 'saved3.cfg')
        print(QT_CONFIG)
        self.assertEqual(QT_CONFIG.mode, 2)
        qt.reset_config()
        print(QT_CONFIG)
        self.assertEqual(QT_CONFIG.mode, 1)

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


if __name__ == '__main__':
    unittest.main()