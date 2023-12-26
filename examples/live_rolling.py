# coding=utf-8
# ======================================
# Package:  qteasy
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2023-12-24
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
    alpha = qt.get_built_in_strategy('ndaychg')  # 一个基于N日涨跌幅的策略，用于多市场轮动策略

    alpha.strategy_run_freq = 'd'  # 每天运行
    alpha.data_freq = 'd'  # 日频数据
    alpha.window_length = 25  # 数据窗口长度为25天

    # 定义选股参数
    alpha.sort_ascending = False  # 优先选择涨幅最大的股票
    alpha.condition = 'greater'  # 筛选出涨幅大于某一个值的股票
    alpha.ubound = 0.0  # 筛选出过去20天涨幅大于0%的股票
    alpha.max_sel_count = 2  # 每次最多选出2支股票
    alpha.weighting = 'even'  # 选出的股票等权重买入且权重平均分配

    op = Operator(strategies=[alpha], signal_type='PT', op_type='step')
    op.set_parameter('alpha', (20, ))  # 以20日张跌幅为选股因子

    asset_pool = [  # 4个ETF之间轮，最多同时选中两个
        '515630.SH',  # 保险证券ETF
        '518680.SH',  # 金ETF
        '513100.SH',  # 纳指ETF
        '512000.SH',  # 券商ETF
    ]

    qt.configure(
            mode=0,
            time_zone='Asia/Shanghai',
            asset_type='E',
            asset_pool=asset_pool,
            benchmark_asset='000300.SH',
            trade_batch_size=0.1,  # 基金交易允许0.1份
            sell_batch_size=0.1,  # 基金交易允许0.1份
            live_trade_account_id=args.account,
            live_trade_account=args.new_account,
            live_trade_debug_mode=args.debug,
            live_trade_broker_type='simulator',
            live_trade_broker_params=None,
    )
    datasource = qt.QT_DATA_SOURCE

    if args.restart:
        # clean up all account data in datasource
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if datasource.table_data_exists(table):
                datasource.drop_table_data(table)

    op.run()
