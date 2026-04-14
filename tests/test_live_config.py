# coding=utf-8
# ======================================
# File: test_live_config.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-12
# Desc:
# Unittest for LiveTradeConfig and build_live_trade_config (S1.3 P2).
# ======================================

from __future__ import annotations

import json
import unittest
import warnings

from qteasy._arg_validators import ConfigDict
from qteasy.broker import SimulatorBroker
from qteasy.live_config import LiveTradeConfig, build_live_trade_config
from qteasy.trader import Trader

from tests.trader_test_helpers import (
    create_operator,
    create_test_datasource,
    default_trader_kwargs,
)


def _minimal_valid_live_mapping() -> dict:
    """供 build_live_trade_config 使用的最小合法配置（键与 run_live_trade 消费字段对齐）。"""
    return {
        'asset_pool': '000001.SZ',
        'asset_type': 'E',
        'time_zone': 'Asia/Shanghai',
        'market_open_time_am': '09:30:00',
        'market_close_time_am': '11:30:00',
        'market_open_time_pm': '13:00:00',
        'market_close_time_pm': '15:00:00',
        'live_price_acquire_channel': 'eastmoney',
        'live_price_acquire_freq': '15MIN',
        'live_trade_data_refill_channel': 'eastmoney',
        'live_trade_data_refill_batch_size': 0,
        'live_trade_data_refill_batch_interval': 0,
        'watched_price_refresh_interval': 5,
        'benchmark_asset': '000300.SH',
        'PT_buy_threshold': 0.05,
        'PT_sell_threshold': 0.05,
        'allow_sell_short': False,
        'trade_batch_size': 0.01,
        'sell_batch_size': 0.01,
        'long_position_limit': 1.0,
        'short_position_limit': -1.0,
        'stock_delivery_period': 1,
        'cash_delivery_period': 0,
        'strategy_open_close_timing_offset': 1,
        'live_trade_daily_refill_tables': 'stock_daily',
        'live_trade_weekly_refill_tables': '',
        'live_trade_monthly_refill_tables': '',
        'live_trade_broker_type': 'simulator',
        'live_trade_broker_params': None,
        'live_trade_ui_type': 'cli',
        'live_trade_account_id': 1,
    }


class TestBuildLiveTradeConfig(unittest.TestCase):
    """A–H：构建、覆盖、校验、摘要。"""

    def test_build_maps_config_keys_to_live_trade_config_fields(self) -> None:
        print('\n[TestBuildLiveTradeConfig] A1 explicit field mapping')
        base = _minimal_valid_live_mapping()
        base['live_trade_broker_type'] = 'simple'
        base['live_price_acquire_channel'] = 'tushare'
        base['live_price_acquire_freq'] = '1MIN'
        base['live_trade_data_refill_channel'] = 'tushare'
        base['market_open_time_am'] = '09:31:00'
        cfg = build_live_trade_config(base)
        print(' cfg:', cfg)
        expected_broker = 'simple'
        expected_lpc = 'tushare'
        expected_freq = '1MIN'
        expected_refill = 'tushare'
        expected_mo_am = '09:31:00'
        expected_asset_type = 'E'
        self.assertEqual(cfg.live_trade_broker_type, expected_broker)
        self.assertEqual(cfg.live_price_acquire_channel, expected_lpc)
        self.assertEqual(cfg.live_price_acquire_freq, expected_freq)
        self.assertEqual(cfg.live_trade_data_refill_channel, expected_refill)
        self.assertEqual(cfg.market_open_time_am, expected_mo_am)
        self.assertEqual(cfg.asset_type, expected_asset_type)
        self.assertEqual(cfg.live_trade_daily_refill_tables, 'stock_daily')
        self.assertEqual(cfg.pt_buy_threshold, 0.05)

    def test_build_normalizes_broker_type_and_ui_type_case(self) -> None:
        print('\n[TestBuildLiveTradeConfig] A2 broker/ui normalization')
        base = _minimal_valid_live_mapping()
        base['live_trade_broker_type'] = 'SimuLator'
        base['live_trade_ui_type'] = 'CLI'
        cfg = build_live_trade_config(base)
        print(' broker/ui:', cfg.live_trade_broker_type, cfg.live_trade_ui_type)
        self.assertEqual(cfg.live_trade_broker_type, 'simulator')
        self.assertEqual(cfg.live_trade_ui_type, 'cli')
        self.assertIn(cfg.live_trade_broker_type, {'simulator', 'simple', 'manual', 'random'})

    def test_build_accepts_random_broker_with_deprecation_warning(self) -> None:
        print('\n[TestBuildLiveTradeConfig] A3 random broker FutureWarning')
        base = _minimal_valid_live_mapping()
        base['live_trade_broker_type'] = 'random'
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            cfg = build_live_trade_config(base)
        self.assertIsInstance(cfg, LiveTradeConfig)
        self.assertEqual(cfg.live_trade_broker_type, 'random')
        self.assertTrue(len(w) >= 1)
        self.assertEqual(w[0].category, FutureWarning)
        msg = str(w[0].message)
        print(' warning:', msg)
        self.assertTrue(msg.isascii())
        self.assertIn('deprecated', msg.lower())
        self.assertIn('simulator', msg.lower())

    def test_overrides_replace_base_live_price_channel(self) -> None:
        print('\n[TestBuildLiveTradeConfig] B1 overrides channel')
        base = _minimal_valid_live_mapping()
        print(' base channel:', base['live_price_acquire_channel'])
        print(' override: tushare')
        cfg = build_live_trade_config(base, live_price_acquire_channel='tushare')
        print(' result channel:', cfg.live_price_acquire_channel)
        self.assertEqual(cfg.live_price_acquire_channel, 'tushare')

    def test_overrides_win_on_nested_dict_shallow_only(self) -> None:
        print('\n[TestBuildLiveTradeConfig] B2 shallow merge on broker_params')
        base = _minimal_valid_live_mapping()
        base['live_trade_broker_params'] = {'a': 1, 'b': 2}
        cfg = build_live_trade_config(base, live_trade_broker_params={'a': 3})
        print(' broker_params tuple:', cfg.live_trade_broker_params)
        self.assertEqual(cfg.live_trade_broker_params, (('a', 3),))

    def test_rejects_unknown_broker_type(self) -> None:
        print('\n[TestBuildLiveTradeConfig] C1 unknown broker')
        base = _minimal_valid_live_mapping()
        base['live_trade_broker_type'] = 'qmt'
        with self.assertRaises(ValueError) as ctx:
            build_live_trade_config(base)
        err = str(ctx.exception)
        print(' error:', err)
        self.assertIn('qmt', err.lower())
        self.assertTrue(err.isascii())

    def test_rejects_non_str_broker_type(self) -> None:
        print('\n[TestBuildLiveTradeConfig] C2 non-str broker')
        base = _minimal_valid_live_mapping()
        base['live_trade_broker_type'] = 1  # type: ignore[assignment]
        with self.assertRaises(TypeError) as ctx:
            build_live_trade_config(base)
        self.assertTrue(str(ctx.exception).isascii())

    def test_rejects_malformed_market_time(self) -> None:
        print('\n[TestBuildLiveTradeConfig] D1 malformed time')
        base = _minimal_valid_live_mapping()
        base['market_open_time_am'] = '25:00:00'
        with self.assertRaises(ValueError) as ctx:
            build_live_trade_config(base)
        self.assertIn('market_open_time_am', str(ctx.exception))
        base2 = _minimal_valid_live_mapping()
        base2['market_open_time_am'] = '9:30'
        with self.assertRaises(ValueError) as ctx2:
            build_live_trade_config(base2)
        print(' D1b error:', ctx2.exception)
        self.assertTrue(str(ctx2.exception).isascii())

    def test_allows_standard_exchange_session_times(self) -> None:
        print('\n[TestBuildLiveTradeConfig] D2 standard session times')
        base = _minimal_valid_live_mapping()
        cfg = build_live_trade_config(base)
        self.assertEqual(cfg.market_open_time_am, '09:30:00')
        self.assertEqual(cfg.market_close_time_am, '11:30:00')
        self.assertEqual(cfg.market_open_time_pm, '13:00:00')
        self.assertEqual(cfg.market_close_time_pm, '15:00:00')

    def test_rejects_invalid_live_price_freq(self) -> None:
        print('\n[TestBuildLiveTradeConfig] E1 invalid freq')
        base = _minimal_valid_live_mapping()
        base['live_price_acquire_freq'] = '2MIN'
        with self.assertRaises(ValueError) as ctx:
            build_live_trade_config(base)
        err = str(ctx.exception)
        print(' error:', err)
        self.assertIn('freq', err.lower())
        self.assertTrue(err.isascii())

    def test_accepts_uppercase_allowed_freq(self) -> None:
        print('\n[TestBuildLiveTradeConfig] E2 lowercase input normalized to canonical upper')
        base = _minimal_valid_live_mapping()
        base['live_price_acquire_freq'] = '15min'
        cfg = build_live_trade_config(base)
        print(' canonical freq:', cfg.live_price_acquire_freq)
        self.assertEqual(cfg.live_price_acquire_freq, '15MIN')

    def test_rejects_invalid_live_price_channel(self) -> None:
        print('\n[TestBuildLiveTradeConfig] F1 invalid price channel')
        base = _minimal_valid_live_mapping()
        base['live_price_acquire_channel'] = 'invalid_ch'
        with self.assertRaises(ValueError) as ctx:
            build_live_trade_config(base)
        self.assertTrue(str(ctx.exception).isascii())

    def test_rejects_invalid_refill_channel(self) -> None:
        print('\n[TestBuildLiveTradeConfig] F2 invalid refill channel (case-sensitive)')
        base = _minimal_valid_live_mapping()
        base['live_trade_data_refill_channel'] = 'Eastmoney'
        with self.assertRaises(ValueError) as ctx:
            build_live_trade_config(base)
        self.assertTrue(str(ctx.exception).isascii())

    def test_rejects_trade_batch_size_below_minimum(self) -> None:
        print('\n[TestBuildLiveTradeConfig] G1 trade_batch_size too small')
        base = _minimal_valid_live_mapping()
        base['trade_batch_size'] = 0.001
        with self.assertRaises(ValueError) as ctx:
            build_live_trade_config(base)
        self.assertIn('trade_batch_size', str(ctx.exception))

    def test_allows_trade_batch_size_equal_minimum(self) -> None:
        print('\n[TestBuildLiveTradeConfig] G2 trade_batch_size boundary')
        base = _minimal_valid_live_mapping()
        base['trade_batch_size'] = 0.01
        cfg = build_live_trade_config(base)
        self.assertAlmostEqual(cfg.trade_batch_size, 0.01, places=6)

    def test_rejects_sell_batch_size_below_minimum(self) -> None:
        print('\n[TestBuildLiveTradeConfig] G3 sell_batch_size too small')
        base = _minimal_valid_live_mapping()
        base['sell_batch_size'] = 0.001
        with self.assertRaises(ValueError) as ctx:
            build_live_trade_config(base)
        self.assertIn('sell_batch_size', str(ctx.exception))

    def test_allows_sell_batch_size_equal_minimum(self) -> None:
        print('\n[TestBuildLiveTradeConfig] G4 sell_batch_size boundary')
        base = _minimal_valid_live_mapping()
        base['sell_batch_size'] = 0.01
        cfg = build_live_trade_config(base)
        self.assertAlmostEqual(cfg.sell_batch_size, 0.01, places=6)

    def test_rejects_watched_price_refresh_below_five(self) -> None:
        print('\n[TestBuildLiveTradeConfig] G5 watched_price_refresh_interval')
        base = _minimal_valid_live_mapping()
        base['watched_price_refresh_interval'] = 4
        with self.assertRaises(ValueError):
            build_live_trade_config(base)

    def test_allows_watched_price_refresh_equal_five(self) -> None:
        print('\n[TestBuildLiveTradeConfig] G6 watched_price_refresh_interval=5')
        base = _minimal_valid_live_mapping()
        base['watched_price_refresh_interval'] = 5
        cfg = build_live_trade_config(base)
        self.assertEqual(cfg.watched_price_refresh_interval, 5)

    def test_summary_dict_contains_stable_subset(self) -> None:
        print('\n[TestBuildLiveTradeConfig] H1 summary dict')
        base = _minimal_valid_live_mapping()
        cfg = build_live_trade_config(base)
        summary = cfg.to_summary_dict()
        print(' summary:', summary)
        self.assertEqual(summary['broker_type'], cfg.live_trade_broker_type)
        self.assertEqual(summary['live_price_channel'], cfg.live_price_acquire_channel)
        self.assertEqual(summary['live_price_freq'], cfg.live_price_acquire_freq)
        self.assertEqual(summary['asset_type'], cfg.asset_type)

    def test_summary_dict_is_json_friendly(self) -> None:
        print('\n[TestBuildLiveTradeConfig] H2 JSON serialization')
        base = _minimal_valid_live_mapping()
        cfg = build_live_trade_config(base)
        summary = cfg.to_summary_dict()
        raw = json.dumps(summary)
        print(' json length:', len(raw))
        self.assertIsInstance(raw, str)
        self.assertGreater(len(raw), 10)


class TestTraderLiveConfigIntegration(unittest.TestCase):
    """I：Trader 注入 live_config。"""

    def setUp(self) -> None:
        self.ds = create_test_datasource(legacy=False)

    def tearDown(self) -> None:
        from tests.trader_test_helpers import clear_tables

        clear_tables(self.ds)

    def test_trader_applies_live_config_over_default_kwargs(self) -> None:
        print('\n[TestTraderLiveConfigIntegration] I1 live_config overrides kwargs')
        from qteasy.trade_recording import new_account

        new_account(user_name='lc_u1', cash_amount=100000.0, data_source=self.ds)
        op = create_operator()
        br = SimulatorBroker()
        kwargs = default_trader_kwargs()
        print(' default live_price_channel:', kwargs.get('live_price_channel'))
        self.assertEqual(kwargs['live_price_channel'], 'eastmoney')
        base = _minimal_valid_live_mapping()
        base['live_price_acquire_channel'] = 'tushare'
        base['live_trade_data_refill_batch_size'] = 7
        cfg = build_live_trade_config(base)
        trader = Trader(
            account_id=1,
            operator=op,
            broker=br,
            datasource=self.ds,
            risk_manager=None,
            live_config=cfg,
            **kwargs,
        )
        print(' trader.live_price_channel:', trader.live_price_channel)
        print(' trader.live_data_batch_size:', trader.live_data_batch_size)
        self.assertEqual(trader.live_price_channel, 'tushare')
        self.assertEqual(trader.live_data_batch_size, 7)
        self.assertNotEqual(trader.live_price_channel, kwargs['live_price_channel'])

    def test_trader_live_config_none_preserves_legacy_path(self) -> None:
        print('\n[TestTraderLiveConfigIntegration] I2 live_config None')
        from qteasy.trade_recording import new_account

        new_account(user_name='lc_u2', cash_amount=100000.0, data_source=self.ds)
        op = create_operator()
        br = SimulatorBroker()
        kwargs = default_trader_kwargs()
        trader = Trader(
            account_id=1,
            operator=op,
            broker=br,
            datasource=self.ds,
            live_config=None,
            **kwargs,
        )
        self.assertEqual(trader.live_price_channel, kwargs['live_price_channel'])


class TestOperatorRunLivePrerequisite(unittest.TestCase):
    """J：与 Operator 入口一致的最小校验（不启动 UI）。"""

    def test_run_live_prerequisite_invalid_broker_raises_english_valueerror(self) -> None:
        print('\n[TestOperatorRunLivePrerequisite] J1 invalid broker before shell')
        cfg = _minimal_valid_live_mapping()
        cfg['live_trade_broker_type'] = 'invalid_broker_x'
        cfg['cost_rate_buy'] = 0.0003
        cfg['cost_rate_sell'] = 0.0003
        cfg['cost_min_buy'] = 5.0
        cfg['cost_min_sell'] = 5.0
        cfg['cost_slippage'] = 0.0
        cfg['live_trade_init_holdings'] = None
        cfg['mode'] = 0
        with self.assertRaises(ValueError) as ctx:
            build_live_trade_config(cfg)
        err = str(ctx.exception)
        print(' error:', err)
        self.assertTrue(err.isascii())
        self.assertIn('invalid_broker_x', err.lower())

    def test_run_live_trade_configdict_accepted(self) -> None:
        print('\n[TestOperatorRunLivePrerequisite] J2 ConfigDict')
        cd = ConfigDict(_minimal_valid_live_mapping())
        cfg = build_live_trade_config(cd)
        self.assertIsInstance(cfg, LiveTradeConfig)
        self.assertEqual(cfg.asset_type, 'E')


if __name__ == '__main__':
    unittest.main()
