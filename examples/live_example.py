# coding=utf-8
# ======================================
# Package:  qteasy
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-12-11
# Desc:
#   live_rolling:
#   一个用于ETF基金的多市场轮动
# 交易策略略，同时监控多只ETF基
# 金，轮动持有20日涨幅最大的两只。
# ======================================


import os
import sys
sys.path.insert(0, os.path.abspath('../'))

if __name__ == '__main__':
    import qteasy as qt
    from qteasy import Operator
    from qteasy.utilfuncs import get_qt_argparser
    parser = get_qt_argparser()
    args = parser.parse_args()

    # 内置交易策略，使用macd执行交易
    alpha = qt.get_built_in_strategy('macd')

    alpha.strategy_run_freq = '10min'  # 每10分钟运行
    alpha.data_freq = '10min'  # 10min数据
    alpha.window_length = 100  # 数据窗口长度

    beta = qt.get_built_in_strategy('dma')

    beta.strategy_run_freq = '30min'  # 每30分钟运行
    beta.data_freq = '30min'  # 30min数据
    beta.window_length = 100  # 数据窗口长度

    op = Operator(strategies=[alpha, beta], signal_type='PT', op_type='step')

    op.set_parameter('alpha', (32, 16, 9))
    op.set_parameter('beta', (10, 50, 10))

    asset_pool = ['000651.SZ', '688609.SH', '000550.SZ', '301215.SZ', '002676.SZ', '603726.SH']

    datasource = qt.QT_DATA_SOURCE
    if args.restart:
        # clean up all trade data in current account
        from qteasy.trade_recording import delete_account
        delete_account(account_id=args.account, data_source=datasource, keep_account_id=True)

    qt.configure(
            mode=0,
            time_zone='Asia/Shanghai',
            asset_type='E',
            asset_pool=asset_pool,
            benchmark_asset='000001.SH',
            benchmark_asset_type='IDX',
            benchmark_dtype='close',
            trade_batch_size=100,
            sell_batch_size=100,
            live_trade_account_id=args.account,
            live_trade_account_name=args.new_account,
            live_trade_debug_mode=args.debug,
            live_trade_broker_type='simulator',
            live_trade_ui_type=args.ui,
            live_trade_broker_params=None,
    )

    op.run()
