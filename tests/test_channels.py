# coding=utf-8
# ======================================
# File:     test_channels.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2024-12-25
# Desc:
#   Testing download data from different
# data channels for every possible data
# table in the test datasource.
#   全量通道表遍历（test_get_table_data_from_channels）在 setUp 中将
#   hist_dnld_retry_cnt=1、wait=0.1、backoff=1；遇权限或 eastmoney 公网
#   HTTP 不可恢复错误时跳过当前表并中止该通道剩余表（生产 refill 不受影响）。
# ======================================

import logging
import unittest
import time
import warnings
from datetime import date
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pandas as pd

import qteasy as qt
from qteasy.database import DataSource
from qteasy.utilfuncs import (
    classify_download_error,
    download_error_should_not_retry,
)
from qteasy.data_channels import (
    EASTMONEY_API_MAP, TUSHARE_API_MAP, AKSHARE_API_MAP,
    _get_fetch_table_func,
    _hist_dnld_thread_pool_max_workers,
    fetch_batched_table_data,
    fetch_real_time_klines,
    fetch_real_time_quotes,
    _parse_list_args,
    _parse_datetime_args,
    _parse_trade_date_args,
    _parse_quarter_args,
    _parse_month_args,
    _parse_table_index_args,
    _parse_additional_time_args,
    _ensure_date_sequence,
    parse_data_fetch_args,
    get_dependent_table,
    list_builtin_channels,
    list_channel_tables,
    get_table_fetch_spec,
)

ChannelFullTableTestAction = str  # 'skip_table' | 'abort_channel' | 'raise'


def channel_full_table_test_action(channel: str, exc: BaseException) -> ChannelFullTableTestAction:
    """全量通道表遍历测试：表级跳过、通道级中止或向上抛出。"""
    kind = classify_download_error(exc, channel=channel)
    if kind == 'other':
        return 'raise'
    if channel == 'tushare' and kind == 'permission':
        return 'abort_channel'
    if channel == 'eastmoney' and kind == 'transient_http':
        return 'abort_channel'
    return 'skip_table'


def _eastmoney_log_test_action(messages: list[str]) -> ChannelFullTableTestAction:
    """根据 emfuncs 捕获的 warning 判断 eastmoney 全量测试动作。"""
    for msg in messages:
        if classify_download_error(Exception(msg), channel='eastmoney') == 'transient_http':
            return 'abort_channel'
    return 'raise'


class _EastmoneyLogCapture(logging.Handler):
    """捕获 emfuncs 在 HTTP 失败时写入的 warning 文案。"""

    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


class TestChannels(unittest.TestCase):

    def setUp(self):
        """快照 hist_dnld 重试相关全局配置，全量通道测试使用激进重试参数。"""
        self._snap_hist_dnld_retry_cnt = qt.QT_CONFIG.get('hist_dnld_retry_cnt')
        self._snap_hist_dnld_retry_wait = qt.QT_CONFIG.get('hist_dnld_retry_wait')
        self._snap_hist_dnld_backoff = qt.QT_CONFIG.get('hist_dnld_backoff')
        qt.configure(
                hist_dnld_retry_cnt=1,
                hist_dnld_retry_wait=0.1,
                hist_dnld_backoff=1.0,
        )
        print(
                '\n[TestChannels.setUp] hist_dnld retry for channel tests:',
                qt.QT_CONFIG['hist_dnld_retry_cnt'],
                qt.QT_CONFIG['hist_dnld_retry_wait'],
                qt.QT_CONFIG['hist_dnld_backoff'],
        )
        self.ds = DataSource(
            'db',
            host=qt.QT_CONFIG['test_db_host'],
            port=qt.QT_CONFIG['test_db_port'],
            user=qt.QT_CONFIG['test_db_user'],
            password=qt.QT_CONFIG['test_db_password'],
            db_name=qt.QT_CONFIG['test_db_name'],
            allow_drop_table=True,
        )
        print('test datasource created.')

    def tearDown(self) -> None:
        """恢复 hist_dnld 重试配置，避免污染同进程其它测试。"""
        qt.configure(
                hist_dnld_retry_cnt=self._snap_hist_dnld_retry_cnt,
                hist_dnld_retry_wait=self._snap_hist_dnld_retry_wait,
                hist_dnld_backoff=self._snap_hist_dnld_backoff,
        )
        print(
                '\n[TestChannels.tearDown] restored hist_dnld retry:',
                qt.QT_CONFIG['hist_dnld_retry_cnt'],
                qt.QT_CONFIG['hist_dnld_retry_wait'],
                qt.QT_CONFIG['hist_dnld_backoff'],
        )

    def test_get_table_data_from_channels(self):
        """从各通道拉取小样本并写入测试库。

        Eastmoney 通道说明：``EASTMONEY_API_MAP`` 中 ``fund_*`` / ``index_*`` 等表名
        与 ``stock_*`` 共用同一套 ``emfuncs`` 函数（仅 ``qt_code`` 不同），映射元组
        第一项是底层 API 名而非目标表名；日志里应区分 ``target_table`` 与 ``emfuncs_api``。
        """

        channels_to_test = ['tushare', 'eastmoney']
        # channels_to_test = ['eastmoney']

        for channel in channels_to_test:

            if channel == 'tushare':
                all_tables = TUSHARE_API_MAP.keys()
                API_MAP = TUSHARE_API_MAP
            elif channel == 'eastmoney':
                all_tables = EASTMONEY_API_MAP.keys()
                API_MAP = EASTMONEY_API_MAP
            elif channel == 'akshare':
                all_tables = AKSHARE_API_MAP.keys()
                API_MAP = AKSHARE_API_MAP
            else:
                raise KeyError(f'')

            self.assertIsInstance(self.ds, DataSource)

            # if there already are tables existing in the datasource, drop them
            print('dropping tables in the test database...')
            deleted = 0
            for table in all_tables:
                if self.ds.table_data_exists(table):
                    # these data can be retained for further testing
                    self.ds.drop_table_data(table)
                    deleted += 1
                    print(f'table {table} dropped.')
            print(f'{deleted} tables dropped.')

            channel_aborted = False
            for table in all_tables:
                if channel_aborted:
                    break

                # get all tables in the API mapping
                api_name = API_MAP[table][0]
                arg_name = API_MAP[table][1]
                arg_type = API_MAP[table][2]
                arg_range = API_MAP[table][3]

                # parse the filling args and pick the first filling arg value from the range
                if arg_name == 'none':
                    arg_name = None
                    arg_value = None
                else:
                    if arg_type == 'list':
                        from qteasy.utilfuncs import str_to_list
                        range_list = str_to_list(arg_range)
                        arg_value = range_list[0]
                    elif arg_type == 'datetime':
                        arg_value = '20210226'
                    elif arg_type == 'trade_date':
                        arg_value = '20210226'  # 这个交易日是特意选择的，因为它既是一个交易日，也同时是一周/一月内的最后一个交易日
                    elif arg_type == 'us_trade_date':
                        warnings.warn('US trade date is not yet implemented, will implement later')
                        continue
                    elif arg_type == 'hk_trade_date':
                        warnings.warn('HK trade date is not yet implemented, will implement later')
                        continue
                    elif arg_type == 'quarter':
                        arg_value = '2020Q4'
                    elif arg_type == 'month':
                        arg_value = '202102'
                    elif arg_type == 'table_index' and arg_range == 'stock_basic':
                        arg_value = '000651.SZ'
                    elif arg_type == 'table_index' and arg_range == 'index_basic':
                        arg_value = '000001.SH'
                    elif arg_type == 'table_index' and arg_range == 'fund_basic':
                        arg_value = '531300.SH'
                    elif arg_type == 'table_index' and arg_range == 'future_basic':
                        arg_value = 'IF2009.CCFX'
                    elif arg_type == 'table_index' and arg_range == 'opt_basic':
                        arg_value = '10001234.SH'
                    elif arg_type == 'table_index' and arg_range == 'ths_index_basic':
                        arg_value = '700031.TI'
                    else:
                        raise ValueError('unexpected arg type:', arg_type)

                # build the args dict
                if arg_name is not None:
                    kwargs = {arg_name: arg_value}
                else:
                    kwargs = {}

                if channel == 'eastmoney':
                    kwargs['start'] = '20241231'
                    kwargs['end'] = '20250110'

                api_label = (
                    f'emfuncs.{api_name}()'
                    if channel == 'eastmoney' and api_name != table
                    else api_name
                )
                print(
                    f'downloading channel="{channel}" target_table="{table}" '
                    f'emfuncs_api="{api_label}" kwargs={kwargs}'
                )

                fetch_table_data_function = _get_fetch_table_func(channel=channel)
                em_log_capture = None
                em_logger = None
                if channel == 'eastmoney':
                    em_log_capture = _EastmoneyLogCapture()
                    em_logger = logging.getLogger('qteasy.emfuncs')
                    em_logger.addHandler(em_log_capture)
                try:
                    dnld_data = fetch_table_data_function(table, **kwargs)
                except Exception as e:
                    action = channel_full_table_test_action(channel, e)
                    if action == 'abort_channel':
                        print(
                            f'\n[SKIP] channel="{channel}" target_table="{table}" '
                            f'emfuncs_api="{api_label}": unrecoverable fetch error — {e}'
                        )
                        print(
                            f'[SKIP] channel="{channel}": aborting remaining tables '
                            f'after unrecoverable fetch failure'
                        )
                        channel_aborted = True
                        break
                    if action == 'skip_table':
                        print(
                            f'\n[SKIP] channel="{channel}" target_table="{table}" '
                            f'emfuncs_api="{api_label}": channel access or transient network — {e}'
                        )
                        continue
                    print(f'error downloading data for table {table}: {e}')
                    raise
                finally:
                    if em_logger is not None and em_log_capture is not None:
                        em_logger.removeHandler(em_log_capture)

                if channel == 'eastmoney' and em_log_capture is not None:
                    log_action = _eastmoney_log_test_action(em_log_capture.messages)
                    if log_action == 'abort_channel':
                        print(
                            f'\n[SKIP] channel="{channel}" target_table="{table}" '
                            f'emfuncs_api="{api_label}": eastmoney transient HTTP failure '
                            f'(warning logged during this table fetch)'
                        )
                        print(
                            f'[SKIP] channel="{channel}": aborting remaining tables '
                            f'after eastmoney transient HTTP failure'
                        )
                        channel_aborted = True
                        break

                print(f'{len(dnld_data)} rows of data downloaded:\n{dnld_data.head()}')

                # TODO: clean up the data, making it ready to be written to the datasource
                #  from qteasy.database import get_built_in_table_schema, set_primary_key_frame
                #  columns, dtypes, primary_keys, pk_dtypes = get_built_in_table_schema(table)
                #  ready_data = set_primary_key_frame(dnld_data, primary_keys, pk_dtypes)
                #  These should be done with data_channel.scrub_data() function
                ready_data = dnld_data

                # write data to datasource
                self.ds.update_table_data(table, ready_data, merge_type='update')
                data = self.ds.read_table_data(table)
                print('data written to database:', data.head())

    def test_get_dependent_table(self):
        """ test function get_dependent_table"""
        self.assertEqual(get_dependent_table('stock_daily', 'tushare'), 'trade_calendar')
        self.assertEqual(get_dependent_table('index_daily', 'tushare'), 'index_basic')
        self.assertEqual(get_dependent_table('cn_cpi', 'tushare'), None)
        self.assertEqual(get_dependent_table('ths_index_daily', 'tushare'), 'trade_calendar')
        self.assertEqual(get_dependent_table('trade_calendar', 'tushare'), None)

    def test_arg_parsing(self):
        """testing parsing of filling args"""

        print('testing parsing list type args')
        arg_range = 'A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z'
        list_arg_filter = 'A, B, E'

        res = list(_parse_list_args(arg_range, list_arg_filter))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'E'])

        list_arg_filter = ['A', 'B', 'E']
        res = list(_parse_list_args(arg_range, ['A', 'B', 'E'], reversed_par_seq=True))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['E', 'B', 'A'])

        list_arg_filter = 'A:E'
        res = list(_parse_list_args(arg_range, 'A:E', reversed_par_seq=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C', 'D', 'E'])

        list_arg_filter = 'D:A'
        res = list(_parse_list_args(arg_range, 'D:A', reversed_par_seq=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C', 'D'])

        list_arg_filter = None
        res = list(_parse_list_args(arg_range, None, reversed_par_seq=True))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['Z', 'Y', 'X', 'W', 'V', 'U', 'T', 'S', 'R', 'Q', 'P', 'O', 'N', 'M', 'L', 'K',
                               'J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
        )

        list_arg_filter = 'A:C:P'
        res = list(_parse_list_args(arg_range, 'A:C:P', reversed_par_seq=False))
        print(f'arg filter: {list_arg_filter}:\n{res}')
        self.assertEqual(res, ['A', 'B', 'C'])

        # testing error handling:
        with self.assertRaises(Exception):
            list(_parse_list_args(arg_range, ['A:Z:1'], reversed_par_seq=False))
            list(_parse_list_args(arg_range, 35, reversed_par_seq=False))

        print('testing parsing datetime type args')
        arg_range = '20210101'

        start, end = '20210201', '20210210'
        res = _parse_datetime_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210201', '20210202', '20210203', '20210204', '20210205', '20210206',
                               '20210207', '20210208', '20210209', '20210210'])

        start, end = '20201220', '20210105'
        res = _parse_datetime_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210101', '20210102', '20210103', '20210104', '20210105'])

        start, end = '20201220', '20210105'
        res = _parse_datetime_args(arg_range, start, end, reversed_par_seq=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210105', '20210104', '20210103', '20210102', '20210101'])

        start, end = '20210110', '20210105'
        res = _parse_datetime_args(arg_range, start, end, reversed_par_seq=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210110', '20210109', '20210108', '20210107', '20210106', '20210105'])

        start, end, freq = '20210101', '20210201', 'W'
        res = _parse_datetime_args(arg_range, start, end, freq=freq)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210101', '20210108', '20210115', '20210122', '20210129'])

        start, end, freq = '20210101', '20210401', 'M'
        res = _parse_datetime_args(arg_range, start, end, freq=freq)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210131', '20210228', '20210331'])

        print('\n[TestChannels] parse_datetime_args accepts date objects (Trader refill path)')
        res = _parse_datetime_args(arg_range, date(2021, 2, 1), date(2021, 2, 5))
        print(' date start/end:', res)
        self.assertEqual(res, ['20210201', '20210202', '20210203', '20210204', '20210205'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_datetime_args(arg_range, 'not_a_date', '20201231')
            _parse_datetime_args(arg_range, '20210101', 20201231)

        print('testing parsing trade_date args')
        arg_range = '20210101'

        start, end = '20210201', '20210210'
        res = _parse_trade_date_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210201', '20210202', '20210203', '20210204', '20210205',
                               '20210208', '20210209', '20210210'])

        start, end = '20201220', '20210105'
        res = _parse_trade_date_args(arg_range, start, end)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210104', '20210105'])

        start, end = '20201220', '20210105'
        res = _parse_trade_date_args(arg_range, start, end, reversed_par_seq=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210105', '20210104'])

        start, end = '20210110', '20210105'
        res = _parse_trade_date_args(arg_range, start, end, reversed_par_seq=True)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210108', '20210107', '20210106', '20210105'])

        start, end, freq = '20210101', '20210201', 'W'
        res = _parse_trade_date_args(arg_range, start, end, freq=freq)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20201231', '20210108', '20210115', '20210122', '20210129'])

        start, end, freq = '20210101', '20210401', 'M'
        res = _parse_trade_date_args(arg_range, start, end, freq=freq)
        print(f'start, end: {start, end}:\n{res}')
        self.assertEqual(res, ['20210129', '20210226', '20210331'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_trade_date_args(arg_range, 'not_a_date', '20201231')
            _parse_trade_date_args(arg_range, '20210101', 20201231)

        print('testing parsing table index args')

        arg_range = 'stock_basic'
        res = _parse_table_index_args(arg_range, symbols='000651.SZ:000660.SZ')
        print(f'symbols: 000651.SZ:000660.SZ:\n{res}')
        self.assertEqual(res, ['000651.SZ', '000652.SZ', '000655.SZ', '000656.SZ', '000657.SZ', '000659.SZ'])

        arg_range = 'stock_basic'
        res = _parse_table_index_args(arg_range, symbols='000651.SZ:000660.SZ', reversed_par_seq=True)
        print(f'symbols: 000651.SZ:000660.SZ:\n{res}')
        self.assertEqual(res, ['000659.SZ', '000657.SZ', '000656.SZ', '000655.SZ', '000652.SZ', '000651.SZ'])

        arg_range = 'stock_basic'
        res = _parse_table_index_args(arg_range, symbols='000651.SZ,000659.SZ, 600000.SH, 600004.SH')
        print(f'symbols: 000651.SZ,000660.SZ, 600001.SH, 600002.SH:\n{res}')
        self.assertEqual(res, ['000651.SZ', '000659.SZ', '600000.SH', '600004.SH'])

        arg_range = 'stock_basic'
        res = _parse_table_index_args(arg_range, symbols='000651.SZ,000659.SZ, 600000.SH, 600004.SH',
                                      allowed_code_suffix='SZ')
        print(f'symbols: 000651.SZ,000659.SZ, 600000.SH, 600004.SH:\n{res}')
        self.assertEqual(res, ['000651.SZ', '000659.SZ'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_table_index_args(arg_range, symbols=651,
                                    allowed_code_suffix='SZ,SH')
            _parse_table_index_args(arg_range, symbols=['000651.SZ:000660.SZ'],
                                    allowed_code_suffix='SZ,SH')

        print('testing parsing quarter and month args')

        arg_range = '2020Q1'
        res = _parse_quarter_args(arg_range, '20200101', '20200930')
        print(f'start, end: 20200101, 20200930:\n{res}')
        self.assertEqual(res, ['2020Q1', '2020Q2', '2020Q3'])

        arg_range = '2020Q1'
        res = _parse_quarter_args(arg_range, '20200101', '20201031')
        print(f'start, end: 20200101, 20201031:\n{res}')
        self.assertEqual(res, ['2020Q1', '2020Q2', '2020Q3', '2020Q4'])

        res = _parse_quarter_args(arg_range, '20210331', '20191021', reversed_par_seq=True)
        print(f'start, end: 2021Q1, 2019Q3:\n{res}')
        self.assertEqual(res, ['2021Q1', '2020Q4', '2020Q3', '2020Q2', '2020Q1'])

        arg_range = '20210101'
        res = _parse_month_args(arg_range, '20210101', '20210331')
        print(f'start, end: 20210101, 20210331:\n{res}')
        self.assertEqual(res, ['202101', '202102', '202103'])
        res = _parse_month_args(arg_range, '20210101', '20210110')
        print(f'start, end: 20210101, 20210110:\n{res}')
        self.assertEqual(res, ['202101'])

        arg_range = '20200901'
        res = _parse_month_args(arg_range, '20200101', '20210530', reversed_par_seq=True)
        print(f'start, end: 20200101, 20210530:\n{res}')
        self.assertEqual(res, ['202105', '202104', '202103', '202102', '202101',
                               '202012', '202011', '202010', '202009'])

        # testing error handling:
        with self.assertRaises(Exception):
            _parse_quarter_args(arg_range, '202001', '2020030')
            _parse_month_args(arg_range, '20200101', 20200930)

        print('testing parsing additional start/end args')
        arg_range = 15
        res = _parse_additional_time_args(arg_range, '20210101', '20210321')
        print(f'start, end: 20210101, 20210321:\n{res}')
        self.assertEqual(
                res,
                [
                    {'end': '20210116', 'start': '20210101'},
                    {'end': '20210131', 'start': '20210116'},
                    {'end': '20210215', 'start': '20210131'},
                    {'end': '20210302', 'start': '20210215'},
                    {'end': '20210317', 'start': '20210302'},
                    {'end': '20210321', 'start': '20210317'},
                ]
        )

        print('\n[TestChannels] ensure_date_sequence defaults when refill dates are None')
        start_dt, end_dt = _ensure_date_sequence('19700101', None, None)
        print(' normalized start:', start_dt, ' end:', end_dt)
        self.assertIsInstance(start_dt, pd.Timestamp)
        self.assertIsInstance(end_dt, pd.Timestamp)
        self.assertEqual(start_dt, pd.Timestamp('1970-01-01'))
        self.assertGreaterEqual(end_dt, start_dt)

        print('\n[TestChannels] additional time args with None refill dates')
        chunks = _parse_additional_time_args(None, None, None)
        print(' single chunk:', chunks)
        self.assertEqual(len(chunks), 1)
        self.assertIn('start', chunks[0])
        self.assertIn('end', chunks[0])

    def test_new_share_parse_args_without_refill_dates(self):
        """basics 中的 new_share 在未传 start/end 时应能解析参数而非 TypeError。"""
        print('\n[TestChannels] new_share parse_data_fetch_args without start/end')
        args = list(parse_data_fetch_args(
            table='new_share',
            channel='tushare',
            symbols=None,
            start_date=None,
            end_date=None,
            list_arg_filter=None,
            reversed_par_seq=False,
        ))
        print(' arg count:', len(args))
        print(' first arg:', args[0] if args else None)
        self.assertGreater(len(args), 0)
        self.assertIn('start', args[0])
        self.assertIn('end', args[0])
        self.assertLessEqual(args[0]['start'], args[0]['end'])

    def test_table_arg_parsing(self):
        """ testing parsing complete table download args """

        table = 'stock_basic'

        print(f'testing parsing args for table: {table}')
        # parse the filling args and pick the first filling arg value from the range
        args = parse_data_fetch_args(table=table,
                                     channel='tushare',
                                     symbols='000651.SZ:000660.SZ',
                                     start_date='20210101',
                                     end_date='20210321',
                                     list_arg_filter=None,
                                     reversed_par_seq=False,
                                     )
        args = list(args)
        print(f'args: {args}')
        self.assertEqual(args, [{'exchange': 'SSE'}, {'exchange': 'SZSE'}, {'exchange': 'BSE'}])

        table = 'stock_daily'
        print(f'testing parsing args for table: {table}')
        # parse the filling args and pick the first filling arg value from the range
        args = parse_data_fetch_args(table=table,
                                     channel='tushare',
                                     symbols='000651.SZ:000660.SZ',
                                     start_date='20210101',
                                     end_date='20210110',
                                     list_arg_filter=None,
                                     reversed_par_seq=False,
                                     )
        args = list(args)
        print(f'args: {args}')
        self.assertEqual(args, [{'trade_date': '20210104'},
                                {'trade_date': '20210105'},
                                {'trade_date': '20210106'},
                                {'trade_date': '20210107'},
                                {'trade_date': '20210108'}])

        table = 'index_daily'
        print(f'testing parsing args for table: {table}')
        # parse the filling args and pick the first filling arg value from the range
        args = parse_data_fetch_args(table=table,
                                     channel='tushare',
                                     symbols='000001.SH, 000011.SH, 000016.SH, 000300.OTHER',
                                     start_date='20210101',
                                     end_date='20210110',
                                     list_arg_filter=None,
                                     reversed_par_seq=False,
                                     )
        args = list(args)
        print(f'args: {args}')
        # 仅保留本地 index_basic 中存在的代码；000300.OTHER 被过滤。
        # 期望含 000011.SH：该指数已写入本地 basics 后应出现在参数序列中。
        self.assertEqual(args, [{'ts_code': '000001.SH', 'start': '20210101', 'end': '20210110'},
                                {'ts_code': '000011.SH', 'start': '20210101', 'end': '20210110'},
                                {'ts_code': '000016.SH', 'start': '20210101', 'end': '20210110'}])

        # parse the filling args and pick the first filling arg value from the range
        args = parse_data_fetch_args(table=table,
                                     channel='tushare',
                                     symbols='000001:000007',
                                     start_date='20210101',
                                     end_date='20210110',
                                     list_arg_filter=None,
                                     reversed_par_seq=False,
                                     )
        args = list(args)
        print(f'args: {args}')
        self.assertEqual(args,
                         [{'end': '20210110', 'start': '20210101', 'ts_code': '000001.SH'},
                          {'end': '20210110', 'start': '20210101', 'ts_code': '000001CNY01.SH'},
                          {'end': '20210110', 'start': '20210101', 'ts_code': '000002.SH'},
                          {'end': '20210110', 'start': '20210101', 'ts_code': '000003.SH'},
                          {'end': '20210110', 'start': '20210101', 'ts_code': '000004.SH'},
                          {'end': '20210110', 'start': '20210101', 'ts_code': '000005.SH'},
                          {'end': '20210110', 'start': '20210101', 'ts_code': '000006.SH'},
                          {'end': '20210110', 'start': '20210101', 'ts_code': '000007.SH'}])

        table = 'index_weight'
        print(f'\n[TestChannels] test_table_arg_parsing: {table} (composite + index + 7d chunks)')
        args = parse_data_fetch_args(table=table,
                                     channel='tushare',
                                     symbols='000001.SH',
                                     start_date='20210101',
                                     end_date='20210110',
                                     list_arg_filter=None,
                                     reversed_par_seq=False,
                                     )
        args = list(args)
        print(f'index_weight args (expect index + start/end per 7d chunk): {args}')
        expected_iw = [
            {'index': '000001.SH', 'start': '20210101', 'end': '20210108'},
            {'index': '000001.SH', 'start': '20210108', 'end': '20210110'},
        ]
        self.assertEqual(args, expected_iw)

        table = 'shibor'  # parse ['shibor', '', '', '', '', 'Y', '365'] type of args
        print(f'testing parsing args for table: {table}')
        # parse the filling args and pick the first filling arg value from the range
        args = parse_data_fetch_args(table=table,
                                     channel='tushare',
                                     symbols='000001.SH, 000011.SH, 000016.SH, 000300.OTHER',
                                     start_date='20210101',
                                     end_date='20220220',
                                     list_arg_filter=None,
                                     reversed_par_seq=False,
                                     )
        args = list(args)
        print(f'args: {args}')
        self.assertEqual(args,
                         [{'start': '20210101', 'end': '20220101'},
                          {'start': '20220101', 'end': '20220220'}])

    def test_fetch_batch_table(self):
        """ test function fetch batch table data"""
        print('testing fetching tables')
        table = 'stock_daily'
        arg_list = parse_data_fetch_args(table=table,
                                         channel='tushare',
                                         symbols='000651.SZ:000660.SZ',
                                         start_date='20210104',
                                         end_date='20210110',
                                         list_arg_filter=None,
                                         reversed_par_seq=False,
                                         )
        for res in fetch_batched_table_data(
                table=table,
                channel='tushare',
                arg_list=arg_list,
                parallel=False,
                process_count=None,
                logger=None
        ):
            df = res['data']
            print(f'kwarg: {res["kwargs"]}, data:\n{df.head()}')
            self.assertIsInstance(df, pd.DataFrame)

        table = 'index_daily'
        arg_list = parse_data_fetch_args(table=table,
                                         channel='tushare',
                                         symbols='000001.SH:000010.SH',
                                         start_date='20210104',
                                         end_date='20210110',
                                         list_arg_filter=None,
                                         reversed_par_seq=False,
                                         )

        print('testing fetching tables with parallel fetching, will start in 5 seconds...')
        time.sleep(5)

        # test parallel fetching
        for res in fetch_batched_table_data(
                table=table,
                channel='tushare',
                arg_list=arg_list,
                parallel=True,
                logger=None
        ):
            df = res['data']
            print(f'kwarg: {res["kwargs"]}, data:\n{df.head()}')
            self.assertIsInstance(df, pd.DataFrame)

    def test_refill_data_source(self):
        """ 测试批量填充多张数据表的数据到测试数据源"""
        from qteasy.core import refill_data_source

        all_tables = TUSHARE_API_MAP.keys()
        # if there already are tables existing in the datasource, drop them
        print('dropping tables in the test database...')
        deleted = 0
        for table in all_tables:
            if table == 'real_time':
                continue
            if self.ds.table_data_exists(table):
                # these data can be retained for further testing
                self.ds.drop_table_data(table)
                deleted += 1
                print(f'table {table} dropped.')
        print(f'{deleted} tables dropped.')

        refill_data_source(
            data_source=self.ds,
            channel='tushare',
            tables='dividend',
            symbols='000001:000020',
            start_date='20240330',
            end_date='20240405',
            parallel=True,
        )

        for table in ['index_5min', 'stock_15min']:
            data = self.ds.read_table_data(table)
            print(f'data written to database for table {table}:\n{data.head()}')

        refill_data_source(
            data_source=self.ds,
            channel='tushare',
            tables='stock_daily, index_daily',
            symbols='000001:000020',
            start_date='20240320',
            end_date='20240325',
            parallel=False,
        )

        for table in ['stock_daily', 'index_daily']:
            data = self.ds.read_table_data(table)
            print(f'data written to database for table {table}:\n{data.head()}')

        refill_data_source(
            data_source=self.ds,
            channel='tushare',
            tables='cn_cpi, index_daily, ths_index_daily',
            symbols='000001:000020',
            start_date='20240326',
            end_date='20240329',
            parallel=True,
        )

        for table in ['cn_cpi', 'ths_index_daily']:
            data = self.ds.read_table_data(table)
            print(f'data written to database for table {table}:\n{data.head()}')

        refill_data_source(
            data_source=self.ds,
            channel='tushare',
            tables='basics',
            dtypes='close, volume',
            freqs='d, m',
            asset_types='E, IDX',
            symbols='000001:000020',
            start_date='20240330',
            end_date='20240405',
            parallel=True,
        )

        for table in ['sw_industry_basic', 'sw_industry_basic', 'new_share', 'fund_basic']:
            data = self.ds.read_table_data(table)
            print(f'data written to database for table {table}:\n{data.head()}')

        # 为节省时间，后面的测试可以不做

        refill_data_source(
            data_source=self.ds,
            channel='tushare',
            tables='events, report, reference',
            symbols='000001:000020',
            start_date='20240330',
            end_date='20240405',
            parallel=True,
        )

        for table in ['libor', 'cn_money', 'hk_top10_stock', 'hs_money_flow', 'top_list', 'stock_suspend',
                      'gz_index', 'cn_sf']:
            data = self.ds.read_table_data(table)
            print(f'data written to database for table {table}:\n{data.head()}')

        refill_data_source(
            data_source=self.ds,
            channel='tushare',
            tables='data, adj',
            symbols='000001:000020',
            start_date='20240330',
            end_date='20240405',
            parallel=True,
        )

        for table in ['index_daily', 'fund_adj_factor']:
            data = self.ds.read_table_data(table)
            print(f'data written to database for table {table}:\n{data.head()}')

        refill_data_source(
            data_source=self.ds,
            channel='tushare',
            tables='mins',
            symbols='000001:000020',
            start_date='20240330',
            end_date='20240405',
            parallel=True,
        )

        for table in ['index_5min', 'stock_15min']:
            data = self.ds.read_table_data(table)
            print(f'data written to database for table {table}:\n{data.head()}')

    def test_realtime_klines(self):
        """testing downloading real-time price data from data-channels"""

        # test acquiring real time data
        channels = ['eastmoney']   #, 'tushare', 'akshare',]
        for channel in channels:
            # test a few stocks
            print(f'Test acquiring 3 stocks from channel {channel}')
            codes = ['000016.SZ', '000025.SZ', '000333.SZ']
            freq = 'd' if channel != 'tushare' else '15min'
            res = fetch_real_time_klines(channel=channel, qt_codes=codes, freq=freq, verbose=False, parallel=False)
            print(f'data acquired from {channel} for codes [\'000016.SZ\', \'000025.SZ\', \'000333.SZ\']: \n{res}')
            self.assertIsInstance(res, pd.DataFrame)
            from qteasy.utilfuncs import is_market_trade_day
            if is_market_trade_day('today'):
                self.assertFalse(res.empty)
                self.assertEqual(res.columns.to_list(), ['ts_code', 'open', 'close', 'high', 'low', 'vol', 'amount'])
                self.assertEqual(res.index.name, 'trade_time')
                self.assertIsInstance(res.index[0], pd.Timestamp)
                self.assertTrue(all(item in codes for item in res.ts_code))
                # some items may not have real time price at the moment
                # self.assertTrue(all(item in res.ts_code.to_list() for item in code))
            else:
                print(f'not a trade day, no real time k-line data acquired!')
                self.assertTrue(res.empty)

            print(f'Test acquiring many prices from channel {channel}')
            code = ['000016.SZ', '000025.SZ', '000333.SZ', '000404.SZ', '000428.SZ', '000521.SZ', '000541.SZ',
                    '000550.SZ', '000572.SZ', '000625.SZ', '000651.SZ', '000721.SZ', '000753.SZ', '000757.SZ',
                    '000810.SZ', '000868.SZ', '000921.SZ', '000951.SZ', '000957.SZ', '000996.SZ', '001259.SZ',
                    '002005.SZ', '002011.SZ', '002032.SZ', '002035.SZ', '002050.SZ', '002076.SZ', '002186.SZ',
                    '002242.SZ', '002290.SZ', '002403.SZ', '002418.SZ', '002420.SZ', '002429.SZ', '002508.SZ',
                    '002543.SZ', '002594.SZ', '002614.SZ', '002668.SZ', '002676.SZ', '002677.SZ', '002705.SZ',
                    '002723.SZ', '002758.SZ', '002759.SZ', '002848.SZ', '002860.SZ', '002959.SZ', '003023.SZ',
                    '300100.SZ', '300160.SZ', '300217.SZ', '300272.SZ', '300342.SZ', '300403.SZ', '300625.SZ',
                    '300808.SZ', '300824.SZ', '300825.SZ', '300894.SZ', '300911.SZ', '301008.SZ', '301039.SZ',
                    '301073.SZ', '301187.SZ', '301215.SZ', '301332.SZ', '301525.SZ', '600006.SH', '600060.SH',
                    '600066.SH', '600099.SH', '600104.SH', '600166.SH', '600213.SH', '600258.SH', '600261.SH',
                    '600297.SH', '600303.SH', '600335.SH', '600336.SH', '600375.SH', '600386.SH', '600418.SH',
                    '600619.SH', '600653.SH', '600686.SH', '600690.SH', '600733.SH', '600754.SH', '600822.SH',
                    '600839.SH', '600854.SH', '600983.SH', '601007.SH', '601127.SH', '601238.SH', '601258.SH',
                    '601633.SH', '601956.SH', '601965.SH', '603195.SH', '603215.SH', '603219.SH', '603303.SH',
                    '603311.SH', '603355.SH', '603366.SH', '603377.SH', '603486.SH', '603515.SH', '603519.SH',
                    '603579.SH', '603657.SH', '603677.SH', '603726.SH', '603868.SH', '605108.SH', '605336.SH',
                    '605365.SH', '605555.SH', '688169.SH', '688609.SH', '688696.SH', '688793.SH', '000801.SZ',]
            res = fetch_real_time_klines(channel=channel, qt_codes=code, freq='5min', verbose=False)
            print(res)
            self.assertIsInstance(res, pd.DataFrame)
            if is_market_trade_day('today'):
                self.assertFalse(res.empty)
                self.assertEqual(res.columns.to_list(), ['ts_code', 'open', 'close', 'high', 'low', 'vol', 'amount'])
                self.assertEqual(res.index.name, 'trade_time')
                self.assertTrue(all(item in code for item in res.ts_code))
                # some items may not have real time price at the moment
                # self.assertTrue(all(item in res.ts_code.to_list() for item in code))
            else:
                print(f'not a trade day, no real time k-line data acquired!')
                self.assertTrue(res.empty)

            print(f'Test acquiring 3 Indexes from channel {channel}')
            codes = ['000001.SH', '000300.SH', '399001.SZ']
            freq = '30min'
            res = fetch_real_time_klines(channel=channel, qt_codes=codes, freq=freq, verbose=True, parallel=False)
            print(res)
            self.assertIsInstance(res, pd.DataFrame)
            if is_market_trade_day('today'):
                self.assertFalse(res.empty)
                self.assertEqual(res.columns.to_list(),
                                 ['ts_code', 'name', 'pre_close', 'open', 'close',
                                  'high', 'low', 'vol', 'amount'])
                self.assertEqual(res.index.name, 'trade_time')
                self.assertTrue(all(item in codes for item in res.ts_code))
                # some items may not have real time price at the moment
                # self.assertTrue(all(item in res.ts_code.to_list() for item in code))
            else:
                print(f'not a trade day, no real time k-line data acquired!')
                self.assertTrue(res.empty)

            print(f'Test acquiring 3 ETF data from channel {channel}')
            codes = ['510050.SH', '510300.SH', '510500.SH', '510880.SH', '510900.SH', '512000.SH', '512010.SH']
            freq = 'h'
            res = fetch_real_time_klines(channel=channel, qt_codes=codes, freq=freq, verbose=False)
            print(res)
            self.assertIsInstance(res, pd.DataFrame)
            if is_market_trade_day('today'):
                self.assertFalse(res.empty)
                self.assertEqual(res.columns.to_list(), ['ts_code', 'open', 'close', 'high', 'low', 'vol', 'amount'])
                self.assertEqual(res.index.name, 'trade_time')
                self.assertTrue(all(item in codes for item in res.ts_code))
                # some items may not have real time price at the moment
                # self.assertTrue(all(item in res.ts_code.to_list() for item in code))
            else:
                print(f'not a trade day, no real time k-line data acquired!')
                self.assertTrue(res.empty)

    def test_realtime_quotes(self):
        """ testing downloading real-time quote data from data channels"""
        # test acquiring real time data
        pass
        # channels = ['tushare', 'eastmoney']
        # for channel in channels:
        #     # test a few stocks
        #     codes = ['000016.SZ', '000025.SZ', '000333.SZ']
        #     res = fetch_real_time_quotes(channel=channel, shares=codes)
        #     print(f'data acquied for codes [\'000016.SZ\', \'000025.SZ\', \'000333.SZ\']: {res}')
        #     self.assertIsInstance(res, pd.DataFrame)
        #     from qteasy.utilfuncs import is_market_trade_day
        #     if is_market_trade_day('today'):
        #         self.assertFalse(res.empty)
        #         self.assertEqual(res.columns.to_list(), ['symbol', 'open', 'close', 'high', 'low', 'vol', 'amount'])
        #         self.assertEqual(res.index.name, 'trade_time')
        #         self.assertTrue(all(item in codes for item in res.symbol))
        #         # some items may not have real time price at the moment
        #         # self.assertTrue(all(item in res.symbol.to_list() for item in code))
        #     else:
        #         print(f'not a trade day, no real time k-line data acquired!')
        #         self.assertTrue(res.empty)


class TestHistDnldParallelWorkers(unittest.TestCase):
    """hist_dnld_parallel 与实时 K 线 / 批量表下载的 ThreadPoolExecutor 接线（不访问外网）。"""

    def setUp(self) -> None:
        import qteasy as qt
        self._saved_hist_dnld_parallel = int(qt.QT_CONFIG['hist_dnld_parallel'])

    def tearDown(self) -> None:
        import qteasy as qt
        qt.configure(hist_dnld_parallel=self._saved_hist_dnld_parallel)

    def test_hist_dnld_thread_pool_max_workers_mapping(self) -> None:
        print('\n[TestHistDnldParallelWorkers] _hist_dnld_thread_pool_max_workers 与 QT_CONFIG')
        import qteasy as qt
        qt.configure(hist_dnld_parallel=0)
        w0 = _hist_dnld_thread_pool_max_workers(None)
        print(' hist_dnld_parallel=0 -> max_workers', w0)
        self.assertEqual(w0, 1)
        qt.configure(hist_dnld_parallel=1)
        w1 = _hist_dnld_thread_pool_max_workers(None)
        print(' hist_dnld_parallel=1 -> max_workers', w1)
        self.assertEqual(w1, 1)
        qt.configure(hist_dnld_parallel=7)
        w7 = _hist_dnld_thread_pool_max_workers(None)
        print(' hist_dnld_parallel=7 -> max_workers', w7)
        self.assertEqual(w7, 7)
        w_explicit = _hist_dnld_thread_pool_max_workers(3)
        print(' process_count=3 -> max_workers', w_explicit)
        self.assertEqual(w_explicit, 3)
        w_zero_explicit = _hist_dnld_thread_pool_max_workers(0)
        print(' process_count=0 -> max_workers', w_zero_explicit)
        self.assertEqual(w_zero_explicit, 1)

    def test_fetch_real_time_klines_parallel_uses_hist_dnld_parallel(self) -> None:
        print('\n[TestHistDnldParallelWorkers] fetch_real_time_klines ThreadPoolExecutor max_workers')
        import qteasy as qt

        def fake_kline(**kwargs):
            idx = pd.DatetimeIndex([pd.Timestamp('2020-01-02 10:00:00')], name='trade_time')
            return pd.DataFrame(
                {
                    'open': [9.0],
                    'close': [10.0],
                    'high': [11.0],
                    'low': [8.0],
                    'vol': [100.0],
                    'amount': [1000.0],
                },
                index=idx,
            )

        qt.configure(hist_dnld_parallel=4)
        with patch('qteasy.data_channels._get_realtime_kline_func', return_value=fake_kline):
            with patch('qteasy.data_channels.ThreadPoolExecutor', wraps=ThreadPoolExecutor) as wrapped_tpe:
                out = fetch_real_time_klines(
                    channel='eastmoney',
                    qt_codes=['000001.SZ', '000002.SZ'],
                    freq='d',
                    verbose=False,
                    parallel=True,
                )
                ca = wrapped_tpe.call_args
                mw = ca.kwargs.get('max_workers') if ca and ca.kwargs else None
                if mw is None and ca and ca.args:
                    mw = ca.args[0]
                print(' ThreadPoolExecutor max_workers:', mw, 'rows:', len(out))
                self.assertEqual(mw, 4)
                self.assertIsInstance(out, pd.DataFrame)
                self.assertEqual(len(out), 2)

    def test_fetch_batched_table_data_parallel_uses_hist_dnld_when_process_count_none(self) -> None:
        print('\n[TestHistDnldParallelWorkers] fetch_batched_table_data ThreadPoolExecutor max_workers')
        import qteasy as qt

        qt.configure(hist_dnld_parallel=3)

        def fake_fetch(table, **kwargs):
            return pd.DataFrame({'x': [1]})

        with patch('qteasy.data_channels._get_fetch_table_func', return_value=fake_fetch):
            with patch('qteasy.data_channels.ThreadPoolExecutor', wraps=ThreadPoolExecutor) as wrapped_tpe:
                rows = list(
                    fetch_batched_table_data(
                        table='stock_basic',
                        channel='tushare',
                        arg_list=[{'a': 1}, {'b': 2}],
                        parallel=True,
                        process_count=None,
                    )
                )
                ca = wrapped_tpe.call_args
                mw = ca.kwargs.get('max_workers') if ca and ca.kwargs else None
                if mw is None and ca and ca.args:
                    mw = ca.args[0]
                print(' max_workers:', mw, 'yielded chunks:', len(rows))
                self.assertEqual(mw, 3)
                self.assertEqual(len(rows), 2)


class TestChannelDiscovery(unittest.TestCase):

    def test_classify_download_error(self) -> None:
        print('\n[TestChannelDiscovery] classify_download_error markers')
        rate_err = Exception('抱歉，您访问接口(stk_mins)频率超限(1次/小时)')
        perm_err = Exception('没有权限访问该接口')
        remote_err = Exception(
            "Eastmoney k-line HTTP request failed: ('Connection aborted.', "
            "RemoteDisconnected('Remote end closed connection without response'))"
        )
        other_err = Exception('connection timeout')
        print(' rate_err kind:', classify_download_error(rate_err))
        print(' perm_err kind:', classify_download_error(perm_err))
        print(' remote_err kind:', classify_download_error(remote_err))
        print(' other_err kind:', classify_download_error(other_err))
        self.assertEqual(classify_download_error(rate_err), 'permission')
        self.assertEqual(classify_download_error(perm_err), 'permission')
        self.assertEqual(classify_download_error(remote_err), 'transient_http')
        self.assertEqual(classify_download_error(other_err), 'other')

    def test_download_error_should_not_retry(self) -> None:
        print('\n[TestChannelDiscovery] download_error_should_not_retry (retry 装饰器对齐)')
        perm_err = Exception('没有访问该接口的权限')
        rate_err = Exception('频率超限')
        print(' perm no-retry:', download_error_should_not_retry(perm_err))
        print(' rate no-retry:', download_error_should_not_retry(rate_err))
        self.assertTrue(download_error_should_not_retry(perm_err))
        self.assertFalse(download_error_should_not_retry(rate_err))

    def test_channel_full_table_test_action(self) -> None:
        print('\n[TestChannelDiscovery] channel_full_table_test_action')
        perm_err = Exception('积分不足')
        remote_err = Exception('Eastmoney k-line HTTP request failed: Connection aborted')
        other_err = Exception('unexpected')
        print(' tushare perm:', channel_full_table_test_action('tushare', perm_err))
        print(' eastmoney http:', channel_full_table_test_action('eastmoney', remote_err))
        print(' tushare other:', channel_full_table_test_action('tushare', other_err))
        self.assertEqual(channel_full_table_test_action('tushare', perm_err), 'abort_channel')
        self.assertEqual(channel_full_table_test_action('eastmoney', remote_err), 'abort_channel')
        self.assertEqual(channel_full_table_test_action('tushare', other_err), 'raise')

    def test_eastmoney_fund_table_maps_to_stock_emfuncs_api(self) -> None:
        """Eastmoney 通道：目标表名与 emfuncs 函数名可不同（共用 K 线接口）。"""
        print('\n[TestChannelDiscovery] eastmoney fund_* -> stock_* emfuncs mapping')
        fund_api = EASTMONEY_API_MAP['fund_15min'][0]
        index_api = EASTMONEY_API_MAP['index_daily'][0]
        print(' fund_15min emfuncs api:', fund_api)
        print(' index_daily emfuncs api:', index_api)
        self.assertEqual(fund_api, 'stock_15min')
        self.assertEqual(index_api, 'stock_daily')

    def test_builtin_channel_listing_and_sina_tables(self):
        print('\n[TestChannelDiscovery] check builtin channels and sina tables')
        channels = list_builtin_channels()
        sina_tables = list_channel_tables('sina')
        ak_tables = list_channel_tables('akshare')
        print(' channels:', channels)
        print(' sina tables sample:', sina_tables[:5])
        print(' akshare tables:', ak_tables)
        self.assertIn('sina', channels)
        self.assertIn('stock_daily', sina_tables)
        self.assertIn('stock_daily', ak_tables)
        self.assertIn('stock_1min', ak_tables)

    def test_akshare_p0_spec_discovery(self) -> None:
        print('\n[TestChannelDiscovery] check AKShare P0 table specs')
        p0_tables = ['stock_daily', 'index_daily', 'fund_daily', 'stock_1min']
        for table in p0_tables:
            spec = get_table_fetch_spec('akshare', table)
            print(
                f' table={table}, api={spec.api}, '
                f'fill_arg={spec.fill_arg_name}/{spec.fill_arg_type}, '
                f'allow_start_end={spec.allow_start_end}'
            )
            self.assertEqual(spec.fill_arg_name, 'qt_code')
            self.assertEqual(spec.fill_arg_type, 'table_index')
            self.assertEqual(spec.allow_start_end.upper(), 'Y')


if __name__ == '__main__':
    unittest.main()
