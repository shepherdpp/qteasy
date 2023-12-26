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

    # 每日选股策略，从一批股票中选出价格高于20日前的
    alpha = qt.get_built_in_strategy('ndayrate')

    alpha.strategy_run_freq = 'd'  # 每日运行
    alpha.data_freq = 'd'  # 日频数据
    alpha.window_length = 20  # 数据窗口长度
    alpha.sort_ascending = False  # 优先选择涨幅最大的股票
    alpha.condition = 'greater'  # 筛选出涨幅大于某一个值的股票
    alpha.ubound = 0.02  # 筛选出过去20天涨幅大于2%的股票
    alpha.max_sel_count = 15  # 每次最多选出10支股票
    alpha.weighting = 'distance'  # 选出的股票买入权重与价格距离成正比

    beta = qt.get_built_in_strategy('finance')

    beta.strategy_run_freq = 'd'  # 每日运行
    beta.data_types = 'pe'  # 数据类型为市盈率
    beta.data_freq = 'd'  # 日频数据
    beta.window_length = 20  # 数据窗口长度
    beta.sort_ascending = True  # 优先选择市盈率较低的股票
    beta.condition = 'between'  # 筛选出市盈率介于某两个值之间的股票，避免选中市盈率过高或过低
    beta.lbound = 1.0  # 市盈率下限
    beta.ubound = 60.  # 市盈率上限
    beta.max_sel_count = 0.75  # 选出75%的股票
    beta.weighting = 'ones'  # 选出的股票等权重买入且权重为100%，防止被选中的股票信号相乘后权重过低

    op = Operator(strategies=[alpha, beta], signal_type='PT', op_type='step')
    op.set_blender(blender='0.75 * unify(s0 * s1)')  # 两个策略的信号相乘后作为最终信号

    asset_pool = qt.filter_stock_codes(industry='家用电器, 汽车整车, 汽车服务, 酒店餐饮', exchange='SSE, SZSE')

    qt.configure(
            mode=0,
            time_zone='Asia/Shanghai',
            asset_type='E',
            asset_pool=asset_pool,
            benchmark_asset='000300.SH',
            benchmark_asset_type='IDX',
            benchmark_dtype='close',
            trade_batch_size=100,
            sell_batch_size=1,
            live_trade_account_id=args.account,
            live_trade_account=args.new_account,
            live_trade_debug_mode=args.debug,
            live_trade_broker_type='random',
            live_trade_broker_params=None,
            watched_price_refresh_interval=10,
    )
    datasource = qt.QT_DATA_SOURCE

    if args.restart:
        # clean up all account data in datasource
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if datasource.table_data_exists(table):
                datasource.drop_table_data(table)

    op.run()
