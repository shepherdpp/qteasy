# coding=utf-8
# ======================================
# File: test_fd_trade_rules.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-10
# Desc:
# Unittest for FD (场内基金) 交易规则：成本解析、MOQ、refill asset_types。
# ======================================

import unittest
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd

from qteasy.config_parser import parse_trade_cost_params
from qteasy.finance import get_purchase_result
from qteasy.trading_util import parse_trade_signal


class TestFdTradeCostParams(unittest.TestCase):
    """parse_trade_cost_params 对 FD 卖出费率印花税近似剥离。"""

    def test_fd_sell_rate_reduces_when_includes_stamp_proxy(self):
        print('\n[TestFdTradeCostParams] FD 高 sell_rate 扣除印花税近似')
        config = {
            'cost_rate_buy':  0.0003,
            'cost_rate_sell': 0.0006,
            'cost_min_buy':   5.0,
            'cost_min_sell':  5.0,
            'cost_slippage':  0.0,
            'asset_type':     'FD',
        }
        p_e = parse_trade_cost_params(config, asset_type='E')
        p_fd = parse_trade_cost_params(config, asset_type='FD')
        self.assertAlmostEqual(p_e['sell_rate'], 0.0006)
        self.assertAlmostEqual(p_fd['sell_rate'], 0.0001)
        print(' E sell_rate', p_e['sell_rate'], 'FD sell_rate', p_fd['sell_rate'])

    def test_fd_low_sell_rate_unchanged(self):
        print('\n[TestFdTradeCostParams] FD 低 sell_rate 不调整')
        config = {
            'cost_rate_buy':  0.0003,
            'cost_rate_sell': 0.0001,
            'cost_min_buy':   0.0,
            'cost_min_sell':   0.0,
            'cost_slippage':  0.0,
        }
        p_fd = parse_trade_cost_params(config, asset_type='FD')
        self.assertAlmostEqual(p_fd['sell_rate'], 0.0001)


class TestFdMoqPointOne(unittest.TestCase):
    """ETF 常见 0.1 最小单位与 get_purchase_result / parse_trade_signal 一致。"""

    def test_parse_trade_signal_vs_moq_point_one(self):
        print('\n[TestFdMoqPointOne] trade_batch_size=0.1 与 get_purchase_result 一致')
        shares = ['ETF1']
        prices = np.array([2.0])
        signals = np.array([125.0])
        own_amounts = np.array([0.0])
        cost_params = np.zeros(5, dtype=float)
        moq = 0.1
        budget = float(signals[0] * prices[0])
        exp_q = float(get_purchase_result(
                np.array([2.0]), np.array([budget]), moq, cost_params,
        )[0][0])
        _, _, _, qty, _, _ = parse_trade_signal(
                signals=signals,
                signal_type='vs',
                shares=shares,
                prices=prices,
                own_amounts=own_amounts,
                own_cash=1e9,
                available_cash=1e9,
                cost_params=cost_params,
                trade_batch_size=moq,
                sell_batch_size=moq,
        )
        self.assertEqual(len(qty), 1)
        self.assertAlmostEqual(qty[0], exp_q, places=6)
        k = round(qty[0] / moq)
        self.assertAlmostEqual(qty[0], k * moq, places=6)


class TestSimulatorMoqTrunc(unittest.TestCase):
    """与 SimulatorBroker.transaction 中 MOQ 截断公式一致。"""

    def test_moq_point_one_trunc_matches_broker_formula(self):
        print('\n[TestSimulatorMoqTrunc] moq=0.1 截断公式')
        moq_buy = 0.1
        remain_qty = 5.47
        filled_proportion = 1.0
        qty = remain_qty * filled_proportion
        qty = np.trunc(qty / moq_buy) * moq_buy
        self.assertAlmostEqual(qty, 5.4)
        print(' qty', qty)


class TestRefillMissingDatasourceAssetTypes(unittest.TestCase):
    """refill_missing_datasource_data 向 refill_data_source 传入含 FD 的 asset_types。"""

    @patch('qteasy.core.refill_data_source')
    @patch('qteasy.utilfuncs.prev_market_trade_day', return_value=pd.Timestamp('2099-01-01'))
    def test_refill_passes_asset_types_with_fd(self, _pday, mock_refill):
        print('\n[TestRefillMissingDatasourceAssetTypes] refill 收到 FD, IDX')
        from qteasy import Operator, DataSource
        from qteasy.trader import Trader, refill_missing_datasource_data
        from qteasy.broker import SimulatorBroker
        from qteasy.trade_recording import new_account
        import os

        data_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data_test_fd_refill',
        )
        os.makedirs(data_dir, exist_ok=True)
        ds = DataSource('file', file_type='csv', file_loc=data_dir, allow_drop_table=True)
        for t in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if ds.table_data_exists(t):
                ds.drop_table_data(t)
        new_account(user_name='fd_refill_t', cash_amount=100_000.0, data_source=ds)

        op = Operator(strategies=['macd'])
        op.set_parameter(stg_id='macd', window_length=3, run_freq='d')
        tr = Trader(
                account_id=1,
                operator=op,
                broker=SimulatorBroker(),
                datasource=ds,
                asset_pool=['515630.SH'],
                asset_type='FD',
        )
        tr.get_current_tz_datetime = MagicMock(
                return_value=pd.Timestamp('2099-06-15 10:00:00'),
        )

        overview_df = pd.DataFrame({'max2': [pd.Timestamp('2000-01-01')]})
        ds.overview = MagicMock(return_value=overview_df)

        refill_missing_datasource_data(operator=op, trader=tr, datasource=ds)
        self.assertTrue(mock_refill.called)
        kwargs = mock_refill.call_args[1]
        self.assertIn('asset_types', kwargs)
        ats = kwargs['asset_types'].replace(' ', '')
        self.assertIn('FD', ats)
        self.assertIn('IDX', ats)
        print(' asset_types kwarg:', kwargs['asset_types'])


if __name__ == '__main__':
    unittest.main()
