# coding=utf-8
# ======================================
# File:     trader_test_helpers.py
# Desc:
#   Trader 相关测试的公共夹具：数据目录、DataSource、Trader 创建等，
#   通过 legacy 参数区分 data_test_trader_legacy 与 data_test_trader。
#   调用方需在测试结束后对 datasource 执行 clear_tables。
# ======================================

import os
import time
from typing import Tuple, Optional, List

import pandas as pd

from qteasy import DataSource, Operator
from qteasy.trade_recording import (
    new_account,
    get_or_create_position,
    update_position,
    save_parsed_trade_orders,
)
from qteasy.trading_util import (
    submit_order,
    process_trade_result,
    cancel_order,
    process_account_delivery,
    deliver_trade_result,
)
from qteasy.trader import Trader
from qteasy.broker import SimulatorBroker


def get_trader_test_data_dir(legacy: bool = False) -> str:
    """返回 Trader 测试用数据目录路径。

    Parameters
    ----------
    legacy : bool, optional
        True 表示 test_trader.py 使用的 data_test_trader_legacy；
        False 表示 test_trader_unit / test_trader_integration 使用的 data_test_trader。
        默认为 False。

    Returns
    -------
    str
        绝对路径。
    """
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    subdir = 'data_test_trader_legacy' if legacy else 'data_test_trader'
    return os.path.join(tests_dir, subdir)


def default_trader_kwargs() -> dict:
    """Trader 测试用默认 kwargs。"""
    return {
        'market_open_time_am': '09:30:00',
        'market_close_time_pm': '15:30:00',
        'market_open_time_pm': '13:00:00',
        'market_close_time_am': '11:30:00',
        'exchange': 'SSE',
        'cash_delivery_period': 0,
        'stock_delivery_period': 0,
        'asset_pool': '000001.SZ, 000002.SZ, 000004.SZ, 000005.SZ, 000006.SZ, 000007.SZ',
        'asset_type': 'E',
        'pt_buy_threshold': 0.05,
        'pt_sell_threshold': 0.05,
        'allow_sell_short': False,
        'live_price_channel': 'eastmoney',
        'live_data_channel': 'eastmoney',
        'live_price_freq': '15min',
        'live_data_batch_size': 0,
        'live_data_batch_interval': 0,
        'daily_refill_tables': 'stock_1min, stock_5min',
        'weekly_refill_tables': 'stock_15min',
        'monthly_refill_tables': 'stock_daily',
    }


def create_operator() -> Operator:
    """创建测试用最小 Operator。"""
    op = Operator(strategies=['macd', 'dma'])
    op.set_parameter(stg_id='dma', window_length=10, run_freq='h')
    op.set_parameter(stg_id='macd', window_length=10, run_freq='30min')
    return op


def clear_tables(datasource: DataSource) -> None:
    """清理测试相关表（账户、持仓、订单、成交、日线等）。"""
    for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders',
                  'sys_op_trade_results', 'stock_daily']:
        if datasource.table_data_exists(table):
            datasource.drop_table_data(table)


def create_test_datasource(legacy: bool = False) -> DataSource:
    """创建专用测试 DataSource，不使用默认 QT_DATA_SOURCE。

    Parameters
    ----------
    legacy : bool, optional
        是否使用 data_test_trader_legacy 目录。默认为 False。

    Returns
    -------
    DataSource
    """
    data_dir = get_trader_test_data_dir(legacy=legacy)
    os.makedirs(data_dir, exist_ok=True)
    return DataSource('file', file_type='csv', file_loc=data_dir, allow_drop_table=True)


def create_trader_with_account(
    account_id: int = 1,
    with_positions: bool = True,
    debug: bool = False,
    legacy: bool = False,
) -> Tuple[Trader, DataSource]:
    """创建带账户（及可选持仓）的 Trader，使用测试 DataSource。

    调用方需在测试结束后对返回的 datasource 执行 clear_tables。

    Parameters
    ----------
    account_id : int, optional
    with_positions : bool, optional
    debug : bool, optional
    legacy : bool, optional
        是否使用 data_test_trader_legacy 目录。默认为 False。

    Returns
    -------
    tuple of (Trader, DataSource)
    """
    test_ds = create_test_datasource(legacy=legacy)
    clear_tables(test_ds)
    new_account(user_name='test_user1', cash_amount=100000, data_source=test_ds)
    if with_positions:
        for sym in ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ']:
            get_or_create_position(account_id=account_id, symbol=sym, position_type='long', data_source=test_ds)
        update_position(position_id=1, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=2, data_source=test_ds, qty_change=200, available_qty_change=200)
        update_position(position_id=3, data_source=test_ds, qty_change=300, available_qty_change=300)
        update_position(position_id=4, data_source=test_ds, qty_change=200, available_qty_change=100)
    operator = create_operator()
    broker = SimulatorBroker()
    trader = Trader(
        account_id=account_id,
        operator=operator,
        broker=broker,
        datasource=test_ds,
        debug=debug,
        **default_trader_kwargs(),
    )
    return trader, test_ds


def create_trader_with_orders_and_results(
    account_id: int = 1,
    debug: bool = False,
    stoppage: float = 0.5,
    legacy: bool = False,
) -> Tuple[Trader, DataSource]:
    """创建带账户、持仓、订单与成交结果的 Trader（完整夹具）。

    两批订单 + 成交与交割。调用方需在测试结束后对返回的 datasource 执行 clear_tables。

    Parameters
    ----------
    account_id : int, optional
    debug : bool, optional
    stoppage : float, optional
        订单/交割之间的 sleep 秒数。
    legacy : bool, optional
        是否使用 data_test_trader_legacy 目录。默认为 False。

    Returns
    -------
    tuple of (Trader, DataSource)
    """
    trader, test_ds = create_trader_with_account(
        account_id=account_id, with_positions=True, debug=debug, legacy=legacy,
    )
    trader.renew_trade_log_file()
    trader.init_system_logger()
    parsed_signals_batch = (
        ['000001.SZ', '000002.SZ', '000004.SZ', '000006.SZ', '000007.SZ'],
        ['long', 'long', 'long', 'long', 'long'],
        ['buy', 'sell', 'sell', 'buy', 'buy'],
        [100, 100, 300, 400, 500],
        [60.0, 70.0, 80.0, 90.0, 100.0],
    )
    order_ids = save_parsed_trade_orders(
        account_id=account_id,
        symbols=parsed_signals_batch[0],
        positions=parsed_signals_batch[1],
        directions=parsed_signals_batch[2],
        quantities=parsed_signals_batch[3],
        prices=parsed_signals_batch[4],
        data_source=test_ds,
    )
    for oid in order_ids:
        submit_order(oid, test_ds)
    time.sleep(stoppage)
    parsed_signals_batch2 = (
        ['000001.SZ', '000004.SZ', '000005.SZ', '000007.SZ'],
        ['long', 'long', 'long', 'long'],
        ['sell', 'buy', 'buy', 'sell'],
        [200, 200, 100, 300],
        [70.0, 30.0, 56.0, 79.0],
    )
    order_ids2 = save_parsed_trade_orders(
        account_id=account_id,
        symbols=parsed_signals_batch2[0],
        positions=parsed_signals_batch2[1],
        directions=parsed_signals_batch2[2],
        quantities=parsed_signals_batch2[3],
        prices=parsed_signals_batch2[4],
        data_source=test_ds,
    )
    for oid in order_ids2:
        submit_order(order_id=oid, data_source=test_ds)
    time.sleep(stoppage)
    delivery_config = {'cash_delivery_period': 0, 'stock_delivery_period': 0}
    for raw in [
        {'order_id': 1, 'filled_qty': 100, 'price': 60.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 2, 'filled_qty': 100, 'price': 70.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 3, 'filled_qty': 200, 'price': 80.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 4, 'filled_qty': 400, 'price': 89.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
        {'order_id': 5, 'filled_qty': 500, 'price': 100.5, 'transaction_fee': 5.0, 'canceled_qty': 0.0},
    ]:
        full = process_trade_result(raw_trade_result=raw, data_source=test_ds)
        trader.log_trade_result(full)
        dr = deliver_trade_result(result_id=full['result_id'], account_id=account_id, data_source=test_ds)
        trader.log_qty_delivery(dr)
        trader.log_cash_delivery(dr)
        time.sleep(stoppage)
    cancel_order(8, test_ds, delivery_config)
    process_account_delivery(account_id=account_id, data_source=test_ds)
    trader.init_trade_log_file()
    trader.init_system_logger()
    return trader, test_ds


def write_minimal_stock_daily(
    datasource: DataSource,
    symbols: Optional[List[str]] = None,
    start_date: str = '2023-02-01',
    end_date: str = '2023-05-10',
) -> None:
    """写入最小日线数据，供 run_strategy 等测试使用。

    每个 symbol 在日期范围内至少 30 根 K 线，列含 ts_code, trade_date, open, high, low, close 等。
    """
    if symbols is None:
        symbols = ['000001.SZ', '000002.SZ', '000004.SZ', '000005.SZ', '000006.SZ', '000007.SZ']
    dates = pd.bdate_range(start=start_date, end=end_date)
    rows = []
    for ts_code in symbols:
        for i, d in enumerate(dates):
            price = 10.0 + (i % 100) * 0.1
            rows.append({
                'ts_code': ts_code,
                'trade_date': d.strftime('%Y-%m-%d'),
                'open': price,
                'high': price + 0.5,
                'low': price - 0.5,
                'close': price + 0.1,
                'pre_close': price - 0.1,
                'change': 0.1,
                'pct_chg': 1.0,
                'vol': 1000000.0,
                'amount': 10000000.0,
            })
    df = pd.DataFrame(rows)
    datasource.write_table_data(df, 'stock_daily')
