# coding=utf-8
# ======================================
# File:     live_grid.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2021-08-29
# Desc:
#   Create a grid trading strategy and
# run the strategy in live mode
# ======================================

import os
import sys

sys.path.insert(0, os.path.abspath('../'))


if __name__ == '__main__':
    from qteasy import Operator
    from qteasy.utilfuncs import get_qt_argparser
    import numpy as np
    import qteasy as qt


    class GridTrade(qt.RuleIterator):
        """网格交易策略"""

        def realize(self):

            # 读取当前保存的策略参数，首次运行时base_grid参数为0，此时买入1000股并设置当前价格为基准网格
            grid_size, trade_batch, base_grid = self.par_values

            # 读取最新价格
            price = self.get_data('close')[-1]  # 最近一个K线周期的close价格
            # 计算当前价格与当前网格的偏离程度，判断是否产生交易信号
            if base_grid <= 0.01:
                # 基准网格尚未设置，此时为首次运行，首次买入2000股并设置基准网格为当前价格（精确到0.1元）
                result = 20000
                base_grid = np.round(price, 1)
            elif price - base_grid > grid_size:
                # 触及卖出网格线，产生卖出信号
                result = - trade_batch  # 交易信号等于交易数量，必须使用VS信号类型
                # 重新计算基准网格
                base_grid += grid_size
            elif base_grid - price > grid_size:
                # 触及买入网格线，产生买入信号
                result = trade_batch + 10.
                # 重新计算基准网格
                base_grid -= grid_size
            else:
                result = 0.

            # 使用新的基准网格更新交易参数
            if not np.isnan(base_grid):
                base_grid = np.round(base_grid, 2)
            self.pars = (grid_size, trade_batch, base_grid)

            return result

    parser = get_qt_argparser()
    args = parser.parse_args()

    alpha = GridTrade(par_values=(0.3, 2000, 38.3),  # 当基准网格为0时，代表首次运行，此时买入1000股，并设置当前价为基准网格
                      pars=[qt.Parameter((0.1, 2), name='grid_size', par_type='float'),
                            qt.Parameter((100, 3000), name='trade_batch', par_type='int'),
                            qt.Parameter((0, 400), name='base_grid', par_type='float')],
                      name='GridTrade',
                      description='网格交易策略，当前股票价格波动幅度超过网格尺寸时，产生卖出或买入交易信号，并更新网格',
                      data_types=[qt.StgData('close', asset_type='E', freq='5min', window_length=20)],
                      )
    op = Operator(alpha, signal_type='VS', op_type='step', run_freq='5min', run_timing='close')

    datasource = qt.QT_DATA_SOURCE
    if args.restart:
        # clean up all trade data in current account
        from qteasy.trade_recording import delete_account
        delete_account(account_id=args.account, data_source=datasource, keep_account_id=True)

    qt.configure(
            mode=0,
            time_zone='Asia/Shanghai',
            asset_type='E',
            asset_pool='000651.SZ',
            benchmark_asset='000651.SZ',
            trade_batch_size=100,
            sell_batch_size=1,
            live_trade_account_id=args.account,
            live_trade_account_name=args.new_account,
            live_trade_debug_mode=args.debug,
            live_trade_broker_type='random',
            live_trade_ui_type=args.ui,
            watched_price_refresh_interval=30,
    )

    qt.run(op)
