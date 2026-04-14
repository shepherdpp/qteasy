# coding=utf-8
# ======================================
# File: test_trade_io_contracts.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-12
# Desc:
# Unittest for qteasy.trade_io order/raw-result dict contracts and validators.
# ======================================

import copy
import sys
import unittest

import numpy as np
import pandas as pd

import qteasy as qt
from qteasy import QT_CONFIG, DataSource
from qteasy.broker import get_broker
from qteasy.trade_io import (
    RAW_RESULT_STATUSES,
    TRADE_ORDER_STATUSES,
    validate_raw_trade_result,
    validate_trade_order,
)
from qteasy.trade_recording import new_account, get_or_create_position, record_trade_order, read_trade_order

from tests.trader_test_helpers import clear_tables, create_trader_with_account


def _base_valid_order() -> dict:
    return {
        'order_id':        1,
        'pos_id':          1,
        'direction':       'buy',
        'order_type':      'limit',
        'qty':             100.0,
        'price':           10.5,
        'status':          'submitted',
        'submitted_time':  '2023-04-09 09:30:00',
    }


def _base_valid_raw_filled() -> dict:
    return {
        'order_id':         1,
        'filled_qty':       100.0,
        'price':            10.5,
        'transaction_fee':  5.0,
        'execution_time':   '2023-04-09 10:00:00',
        'canceled_qty':     0.0,
        'delivery_amount':  0.0,
        'delivery_status':  'ND',
    }


class TestValidateTradeOrder(unittest.TestCase):
    """validate_trade_order 功能与边界。"""

    def test_validate_trade_order_accepts_reference_shape(self):
        print('\n[TestValidateTradeOrder] reference submitted order dict')
        order = _base_valid_order()
        print(' order:', order)
        validate_trade_order(order)
        self.assertGreater(order['order_id'], 0)
        self.assertIn(order['direction'], ('buy', 'sell'))
        self.assertIn(order['order_type'], ('market', 'limit'))
        self.assertGreater(order['qty'], 0)
        self.assertGreater(order['price'], 0)
        self.assertEqual(order['status'], 'submitted')
        self.assertEqual(TRADE_ORDER_STATUSES, frozenset({'submitted'}))

    def test_validate_trade_order_accepts_numpy_integer_pos_id(self):
        print('\n[TestValidateTradeOrder] pos_id as np.int64')
        order = _base_valid_order()
        order['pos_id'] = np.int64(7)
        print(' order:', order)
        validate_trade_order(order)
        self.assertIsInstance(order['pos_id'], (int, np.integer))

    def test_validate_trade_order_accepts_submitted_time_none(self):
        print('\n[TestValidateTradeOrder] submitted_time None')
        order = _base_valid_order()
        order['submitted_time'] = None
        print(' order:', order)
        validate_trade_order(order)

    def test_validate_trade_order_optional_p6_symbol_position_when_present(self):
        print('\n[TestValidateTradeOrder] optional symbol/position valid and invalid')
        ok = _base_valid_order()
        ok['symbol'] = '000001.SZ'
        ok['position'] = 'long'
        print(' ok order:', ok)
        validate_trade_order(ok)
        bad = _base_valid_order()
        bad['position'] = 'mid'
        print(' bad order:', bad)
        with self.assertRaises(ValueError) as cm:
            validate_trade_order(bad)
        self.assertIn('position', str(cm.exception).lower())

    def test_validate_trade_order_rejects_non_dict(self):
        print('\n[TestValidateTradeOrder] non-dict')
        with self.assertRaises(TypeError) as cm:
            validate_trade_order([])  # type: ignore[arg-type]
        msg = str(cm.exception)
        print(' msg:', msg)
        self.assertIn('dict', msg.lower())

    def test_validate_trade_order_rejects_each_missing_required_key(self):
        print('\n[TestValidateTradeOrder] missing each required key')
        for key in (
            'order_id', 'pos_id', 'direction', 'order_type', 'qty', 'price', 'status', 'submitted_time',
        ):
            o = _base_valid_order()
            del o[key]
            print(' missing', key, 'order:', o)
            with self.assertRaises(ValueError) as cm:
                validate_trade_order(o)
            self.assertIn(key, str(cm.exception))

    def test_validate_trade_order_rejects_bad_direction(self):
        print('\n[TestValidateTradeOrder] bad direction')
        o = _base_valid_order()
        o['direction'] = 'hold'
        print(' order:', o)
        with self.assertRaises(ValueError) as cm:
            validate_trade_order(o)
        self.assertIn('direction', str(cm.exception).lower())

    def test_validate_trade_order_rejects_bad_order_type(self):
        print('\n[TestValidateTradeOrder] bad order_type')
        o = _base_valid_order()
        o['order_type'] = 'stop'
        print(' order:', o)
        with self.assertRaises(ValueError) as cm:
            validate_trade_order(o)
        self.assertIn('order_type', str(cm.exception).lower())

    def test_validate_trade_order_rejects_bad_status(self):
        print('\n[TestValidateTradeOrder] bad status')
        o = _base_valid_order()
        o['status'] = 'created'
        print(' order:', o)
        with self.assertRaises(ValueError) as cm:
            validate_trade_order(o)
        self.assertIn('status', str(cm.exception).lower())

    def test_validate_trade_order_rejects_non_positive_qty(self):
        print('\n[TestValidateTradeOrder] qty <= 0')
        o = _base_valid_order()
        o['qty'] = 0
        print(' order:', o)
        with self.assertRaises(ValueError) as cm:
            validate_trade_order(o)
        self.assertIn('qty', str(cm.exception).lower())

    def test_validate_trade_order_rejects_non_positive_price(self):
        print('\n[TestValidateTradeOrder] price <= 0')
        o = _base_valid_order()
        o['price'] = 0.0
        print(' order:', o)
        with self.assertRaises(ValueError) as cm:
            validate_trade_order(o)
        self.assertIn('price', str(cm.exception).lower())

    def test_validate_trade_order_rejects_wrong_numeric_types(self):
        print('\n[TestValidateTradeOrder] qty as str')
        o = _base_valid_order()
        o['qty'] = '100'
        print(' order:', o)
        with self.assertRaises(TypeError) as cm:
            validate_trade_order(o)
        self.assertIn('qty', str(cm.exception).lower())

    def test_validate_trade_order_rejects_empty_symbol_when_present(self):
        print('\n[TestValidateTradeOrder] empty symbol')
        o = _base_valid_order()
        o['symbol'] = '  '
        print(' order:', o)
        with self.assertRaises(ValueError) as cm:
            validate_trade_order(o)
        self.assertIn('symbol', str(cm.exception).lower())


class TestValidateRawTradeResult(unittest.TestCase):
    """validate_raw_trade_result 功能与边界。"""

    def test_validate_raw_trade_result_accepts_filled_reference_shape(self):
        print('\n[TestValidateRawTradeResult] filled reference')
        raw = _base_valid_raw_filled()
        print(' raw:', raw)
        validate_raw_trade_result(raw)
        self.assertGreater(raw['filled_qty'], 0)
        self.assertEqual(raw['canceled_qty'], 0.0)
        self.assertEqual(raw['delivery_status'], 'ND')
        self.assertEqual(RAW_RESULT_STATUSES, frozenset({'filled', 'partial-filled', 'canceled'}))

    def test_validate_raw_trade_result_accepts_canceled_reference_shape(self):
        print('\n[TestValidateRawTradeResult] canceled reference')
        raw = {
            'order_id':         2,
            'filled_qty':       0.0,
            'price':            0.0,
            'transaction_fee':  0.0,
            'execution_time':   '2023-04-09 11:00:00',
            'canceled_qty':     50.0,
            'delivery_amount':  0.0,
            'delivery_status':  'ND',
        }
        print(' raw:', raw)
        validate_raw_trade_result(raw)
        self.assertEqual(raw['filled_qty'], 0.0)
        self.assertEqual(raw['canceled_qty'], 50.0)
        self.assertEqual(raw['price'], 0.0)
        self.assertGreaterEqual(raw['transaction_fee'], 0.0)

    def test_validate_raw_trade_result_optional_p6_fields_when_present(self):
        print('\n[TestValidateRawTradeResult] optional P6 keys')
        raw = copy.deepcopy(_base_valid_raw_filled())
        raw['broker_order_id'] = 'BRK-001'
        raw['status'] = 'filled'
        raw['raw_status'] = 'FILLED'
        print(' raw:', raw)
        validate_raw_trade_result(raw)

    def test_validate_raw_trade_result_optional_p6_bad_broker_order_id(self):
        print('\n[TestValidateRawTradeResult] empty broker_order_id')
        raw = copy.deepcopy(_base_valid_raw_filled())
        raw['broker_order_id'] = ''
        print(' raw:', raw)
        with self.assertRaises(ValueError) as cm:
            validate_raw_trade_result(raw)
        self.assertIn('broker_order_id', str(cm.exception).lower())

    def test_validate_raw_trade_result_optional_p6_bad_status(self):
        print('\n[TestValidateRawTradeResult] invalid optional status')
        raw = copy.deepcopy(_base_valid_raw_filled())
        raw['status'] = 'unknown'
        print(' raw:', raw)
        with self.assertRaises(ValueError) as cm:
            validate_raw_trade_result(raw)
        self.assertIn('status', str(cm.exception).lower())

    def test_validate_raw_trade_result_rejects_non_dict(self):
        print('\n[TestValidateRawTradeResult] non-dict')
        with self.assertRaises(TypeError) as cm:
            validate_raw_trade_result('x')  # type: ignore[arg-type]
        msg = str(cm.exception)
        print(' msg:', msg)
        self.assertIn('dict', msg.lower())

    def test_validate_raw_trade_result_rejects_each_missing_required_key(self):
        print('\n[TestValidateRawTradeResult] missing each required key')
        for key in (
            'order_id',
            'filled_qty',
            'price',
            'transaction_fee',
            'execution_time',
            'canceled_qty',
            'delivery_amount',
            'delivery_status',
        ):
            r = copy.deepcopy(_base_valid_raw_filled())
            del r[key]
            print(' missing', key, 'raw:', r)
            with self.assertRaises(ValueError) as cm:
                validate_raw_trade_result(r)
            self.assertIn(key, str(cm.exception))

    def test_validate_raw_trade_result_rejects_negative_filled_or_canceled_qty(self):
        print('\n[TestValidateRawTradeResult] negative filled_qty')
        r = copy.deepcopy(_base_valid_raw_filled())
        r['filled_qty'] = -1.0
        print(' raw:', r)
        with self.assertRaises(ValueError):
            validate_raw_trade_result(r)

    def test_validate_raw_trade_result_rejects_invalid_delivery_status(self):
        print('\n[TestValidateRawTradeResult] bad delivery_status')
        r = copy.deepcopy(_base_valid_raw_filled())
        r['delivery_status'] = 'XX'
        print(' raw:', r)
        with self.assertRaises(ValueError) as cm:
            validate_raw_trade_result(r)
        self.assertIn('delivery_status', str(cm.exception).lower())

    def test_validate_raw_trade_result_rejects_unparseable_execution_time(self):
        print('\n[TestValidateRawTradeResult] bad execution_time')
        r = copy.deepcopy(_base_valid_raw_filled())
        r['execution_time'] = 'not-a-valid-datetime-%%%'
        print(' raw:', r)
        with self.assertRaises(RuntimeError) as cm:
            validate_raw_trade_result(r)
        self.assertIn('execution_time', str(cm.exception).lower())

    def test_validate_raw_trade_result_rejects_invalid_order_id(self):
        print('\n[TestValidateRawTradeResult] order_id <= 0')
        r = copy.deepcopy(_base_valid_raw_filled())
        r['order_id'] = 0
        print(' raw:', r)
        with self.assertRaises(ValueError) as cm:
            validate_raw_trade_result(r)
        self.assertIn('order_id', str(cm.exception).lower())


class TestTradeIOIntegrationSubmitOrder(unittest.TestCase):
    """submit_trade_order 输出与 read_trade_order 一致性。"""

    def setUp(self) -> None:
        self.trader, self.test_ds = create_trader_with_account(debug=False, legacy=False)

    def tearDown(self) -> None:
        if getattr(self, 'test_ds', None) is not None:
            clear_tables(self.test_ds)

    def test_submit_trade_order_output_passes_validate_trade_order(self):
        print('\n[TestTradeIOIntegrationSubmitOrder] submit_trade_order + validate + DB')
        res = self.trader.submit_trade_order(
            symbol='000001.SZ',
            position='long',
            direction='buy',
            order_type='limit',
            qty=10,
            price=50.0,
        )
        print(' submit_trade_order result:', res)
        self.assertIsInstance(res, dict)
        self.assertIn('order_id', res)
        validate_trade_order(res, context='integration')
        row = read_trade_order(res['order_id'], data_source=self.test_ds)
        print(' read_trade_order row:', row)
        self.assertEqual(row['status'], 'submitted')
        self.assertEqual(res['status'], 'submitted')
        self.assertIsNotNone(res['submitted_time'])


class TestTradeIOIntegrationBrokerGetResult(unittest.TestCase):
    """SimpleBroker._get_result 产出通过 validate_raw_trade_result。"""

    def setUp(self) -> None:
        print('\n[TestTradeIOIntegrationBrokerGetResult] env')
        print(f' python version: {sys.version}')
        print(f' qteasy version: {qt.__version__}')
        print(f' numpy version: {np.__version__}')
        print(f' pandas version: {pd.__version__}')
        self.test_ds = DataSource(
            'db',
            host=QT_CONFIG['test_db_host'],
            port=QT_CONFIG['test_db_port'],
            user=QT_CONFIG['test_db_user'],
            password=QT_CONFIG['test_db_password'],
            db_name=QT_CONFIG['test_db_name'],
            allow_drop_table=True,
        )
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)
        new_account(user_name='test_user', cash_amount=10000.0, data_source=self.test_ds)
        get_or_create_position(1, '000001.SH', 'long', data_source=self.test_ds)
        test_signal = {
            'pos_id':         1,
            'direction':      'buy',
            'order_type':     'limit',
            'qty':            100,
            'price':          100,
            'submitted_time': '2023-04-09 09:30:00',
            'status':         'created',
        }
        self.order_id = record_trade_order(test_signal, data_source=self.test_ds)
        from qteasy.trading_util import submit_order

        submit_order(self.order_id, self.test_ds)

    def tearDown(self) -> None:
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if self.test_ds.table_data_exists(table):
                self.test_ds.drop_table_data(table)

    def test_simulator_get_result_output_passes_validate_raw_trade_result(self):
        print('\n[TestTradeIOIntegrationBrokerGetResult] _get_result + validate_raw')
        bkr = get_broker('simple', params={'data_source': self.test_ds})
        order = dict(read_trade_order(self.order_id, data_source=self.test_ds))
        order['order_id'] = int(self.order_id)
        order['status'] = 'submitted'
        st = order.get('submitted_time')
        if st is not None and not isinstance(st, str):
            order['submitted_time'] = pd.Timestamp(st).strftime('%Y-%m-%d %H:%M:%S')
        order['pos_id'] = int(order['pos_id'])
        print(' order for broker:', order)
        validate_trade_order(order, context='broker_integration')
        bkr._get_result(order)
        result = bkr.result_queue.get()
        print(' result_queue:', result)
        validate_raw_trade_result(result, context='broker_integration')
        self.assertEqual(result['order_id'], self.order_id)
        self.assertEqual(result['filled_qty'], 100.0)
        self.assertEqual(result['price'], 100.0)
        self.assertEqual(result['canceled_qty'], 0.0)
        self.assertEqual(result['transaction_fee'], 5.0)


if __name__ == '__main__':
    unittest.main()
