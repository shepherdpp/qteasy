
import argparse
import numpy as np

import qteasy as qt
from qteasy import QT_CONFIG, DataSource, Operator, RuleIterator


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--account', type=int, help='start trader with the given account id')
    parser.add_argument('-n', '--new_account', type=str, default=None,
                        help='if set, create a new account with the given user name')
    parser.add_argument('-r', '--restart', action='store_true', default=False,
                        help='if set, remove all record and restart account')
    parser.add_argument('-d', '--debug', action='store_true', help='if set, start trader in debug mode')

    args = parser.parse_args()

    alpha = GridTrade(pars=(0.1, 200, 38.0),  # 当基准网格为0时，代表首次运行，此时买入1000股，并设置当前价为基准网格
                      par_count=3,
                      par_types=['float', 'int', 'float'],
                      par_range=[(0.1, 2), (100, 300), (0, 40)],
                      name='GridTrade',
                      description='网格交易策略，当前股票价格波动幅度超过网格尺寸时，产生卖出或买入交易信号，并更新网格',
                      strategy_run_timing='close',
                      strategy_run_freq='5min',
                      data_freq='5min',
                      window_length=20,
                     )

    op = Operator('macd, dma', signal_type='VS', op_type='step')
    qt.configure(
            mode=0,
            asset_type='E',
            asset_pool='000651.SZ',
            benchmark_asset='000651.SZ',
            benchmark_asset_type='E',
            benchmark_dtype='close',
            trade_batch_size=100,
            sell_batch_size=1,
            live_trade_account_id=args.account,
            live_trade_account=args.new_account,
            live_trade_debug_mode=args.debug,
    )
    datasource = qt.QT_DATA_SOURCE

    if args.restart:
        # clean up all account data in datasource
        for table in ['sys_op_live_accounts', 'sys_op_positions', 'sys_op_trade_orders', 'sys_op_trade_results']:
            if datasource.table_data_exists(table):
                datasource.drop_table_data(table)

    op.run()
