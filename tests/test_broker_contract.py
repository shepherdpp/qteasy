# coding=utf-8
# ======================================
# File: test_broker_contract.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-13
# Desc:
# Unittest for Broker adapter contract (S1.3 P6)
# ======================================

import unittest

from qteasy.broker import Broker, SimpleBroker, SimulatorBroker
from qteasy.trade_io import validate_raw_trade_result


class MinimalBrokerForContractTest(Broker):
    """用于契约测试的最小可实例化 Broker。"""

    def __init__(self):
        super().__init__(data_source=None)
        self.broker_name = 'MinimalBroker'

    def _parse_order(self, order):
        """避免访问数据库，直接从订单字典读取字段。"""
        return (
            order['order_type'],
            order.get('symbol', '000001.SH'),
            float(order['qty']),
            float(order['price']),
            order['direction'],
            order.get('position', 'long'),
        )

    def transaction(self, symbol, order_qty, order_price, direction, position='long', order_type='market'):
        half_qty = round(float(order_qty) / 2, 4)
        remain_qty = round(float(order_qty) - half_qty, 4)
        yield 'partial-filled', half_qty, float(order_price), 2.5
        yield 'filled', remain_qty, float(order_price), 2.5


class LegacyMinimalBroker(Broker):
    """用于验证 legacy _get_result 路径金标准。"""

    def __init__(self):
        super().__init__(data_source=None)
        self.broker_name = 'LegacyMinimalBroker'

    def _parse_order(self, order):
        return (
            order['order_type'],
            order.get('symbol', '000001.SH'),
            float(order['qty']),
            float(order['price']),
            order['direction'],
            order.get('position', 'long'),
        )

    def transaction(self, symbol, order_qty, order_price, direction, position='long', order_type='market'):
        yield 'filled', float(order_qty), float(order_price), 5.0


class TestBrokerContract(unittest.TestCase):

    def setUp(self) -> None:
        self.order = {
            'order_id': 1,
            'pos_id': 1,
            'direction': 'buy',
            'order_type': 'limit',
            'qty': 100.0,
            'price': 10.0,
            'status': 'submitted',
            'submitted_time': '2026-04-13 09:30:00',
            'symbol': '000001.SH',
            'position': 'long',
        }

    def test_adapter_methods_exist_on_simulator_and_simple(self):
        print('\n[TestBrokerContract] 检查 Simulator/Simple 新接口存在性')
        for broker in [SimulatorBroker(), SimpleBroker()]:
            for method_name in [
                'connect', 'disconnect', 'submit', 'cancel', 'poll_fills',
                'get_remote_orders', 'get_remote_positions', 'get_remote_cash',
            ]:
                print(f' broker={broker.broker_name}, method={method_name}')
                self.assertTrue(callable(getattr(broker, method_name)))
            self.assertIsNone(broker.connect())
            self.assertIsNone(broker.disconnect())

    def test_submit_returns_non_empty_broker_order_id(self):
        print('\n[TestBrokerContract] submit 返回非空 broker_order_id')
        broker = MinimalBrokerForContractTest()
        broker.connect()
        first_id = broker.submit(self.order)
        second_id = broker.submit(self.order)
        print(' first_id:', first_id)
        print(' second_id:', second_id)
        self.assertIsInstance(first_id, str)
        self.assertGreater(len(first_id), 0)
        self.assertNotEqual(first_id, second_id)

    def test_poll_fills_each_item_passes_validate_raw_trade_result(self):
        print('\n[TestBrokerContract] poll_fills 返回 raw_trade_result 契约')
        broker = MinimalBrokerForContractTest()
        broker.connect()
        broker_order_id = broker.submit(self.order)
        print(' broker_order_id:', broker_order_id)
        all_fills = []
        all_fills.extend(broker.poll_fills())
        all_fills.extend(broker.poll_fills())
        print(' fills:', all_fills)
        self.assertGreaterEqual(len(all_fills), 1)
        for raw in all_fills:
            self.assertEqual(raw['order_id'], self.order['order_id'])
            self.assertGreaterEqual(raw['filled_qty'], 0)
            self.assertGreaterEqual(raw['canceled_qty'], 0)
            self.assertGreaterEqual(raw['transaction_fee'], 0)
            self.assertTrue(raw['delivery_status'])
            validate_raw_trade_result(raw, context='test.poll')

    def test_submit_then_poll_semantics_partial_then_done(self):
        print('\n[TestBrokerContract] submit 同步受理 + poll 异步分批')
        broker = MinimalBrokerForContractTest()
        broker.connect()
        broker.submit(self.order)
        fills_round_1 = broker.poll_fills()
        fills_round_2 = broker.poll_fills()
        print(' round1:', fills_round_1)
        print(' round2:', fills_round_2)
        self.assertEqual(len(fills_round_1), 1)
        self.assertEqual(len(fills_round_2), 1)
        self.assertEqual(fills_round_1[0]['status'], 'partial-filled')
        self.assertEqual(fills_round_2[0]['status'], 'filled')
        total_filled = fills_round_1[0]['filled_qty'] + fills_round_2[0]['filled_qty']
        print(' total_filled:', total_filled, ' expected:', self.order['qty'])
        self.assertAlmostEqual(total_filled, self.order['qty'])
        self.assertEqual(fills_round_1[0]['price'], self.order['price'])
        self.assertEqual(fills_round_2[0]['price'], self.order['price'])

    def test_legacy_queue_get_result_unchanged(self):
        print('\n[TestBrokerContract] legacy _get_result -> result_queue 路径')
        broker = LegacyMinimalBroker()
        broker._get_result(self.order)
        result = broker.result_queue.get()
        print(' legacy result:', result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['order_id'], self.order['order_id'])
        self.assertEqual(result['filled_qty'], self.order['qty'])
        self.assertEqual(result['price'], self.order['price'])
        self.assertEqual(result['transaction_fee'], 5.0)
        validate_raw_trade_result(result, context='test.legacy')

    def test_submit_rejects_invalid_order_dict(self):
        print('\n[TestBrokerContract] submit 拒绝非法订单')
        broker = MinimalBrokerForContractTest()
        broker.connect()
        invalid_order = dict(self.order)
        invalid_order.pop('status')
        with self.assertRaises(ValueError) as cm:
            broker.submit(invalid_order)
        message = str(cm.exception)
        print(' error:', message)
        self.assertIn('Broker.submit.order', message)
        self.assertIn('missing required key', message)

    def test_submit_when_not_connected_raises_runtime_error(self):
        print('\n[TestBrokerContract] 未 connect 调用 submit')
        broker = MinimalBrokerForContractTest()
        with self.assertRaises(RuntimeError) as cm:
            broker.submit(self.order)
        message = str(cm.exception)
        print(' error:', message)
        self.assertIn('not connected', message)

    def test_poll_fills_when_not_connected_raises_runtime_error(self):
        print('\n[TestBrokerContract] 未 connect 调用 poll_fills')
        broker = MinimalBrokerForContractTest()
        with self.assertRaises(RuntimeError) as cm:
            broker.poll_fills()
        message = str(cm.exception)
        print(' error:', message)
        self.assertIn('not connected', message)

    def test_connect_disconnect_idempotent(self):
        print('\n[TestBrokerContract] connect/disconnect 幂等')
        broker = MinimalBrokerForContractTest()
        broker.connect()
        broker.connect()
        broker.disconnect()
        broker.disconnect()
        broker.connect()
        broker_order_id = broker.submit(self.order)
        print(' broker_order_id after reconnect:', broker_order_id)
        self.assertTrue(broker_order_id.startswith('MinimalBroker:'))

    def test_cancel_unknown_broker_order_id(self):
        print('\n[TestBrokerContract] cancel unknown id 返回 False')
        broker = MinimalBrokerForContractTest()
        broker.connect()
        result = broker.cancel('no-such-id')
        print(' cancel result:', result)
        self.assertFalse(result)

    def test_get_remote_apis_stable_empty(self):
        print('\n[TestBrokerContract] remote 查询占位返回稳定类型')
        broker = MinimalBrokerForContractTest()
        orders = broker.get_remote_orders(account_id=1)
        positions = broker.get_remote_positions(account_id=1)
        cash = broker.get_remote_cash(account_id=1)
        print(' orders:', orders)
        print(' positions:', positions)
        print(' cash:', cash)
        self.assertIsInstance(orders, list)
        self.assertEqual(orders, [])
        self.assertIsInstance(positions, list)
        self.assertEqual(positions, [])
        self.assertIsNone(cash)


if __name__ == '__main__':
    unittest.main()
