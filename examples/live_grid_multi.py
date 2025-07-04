# coding=utf-8
# ======================================
# File:     live_grid.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2021-08-29
# Desc:
#   Create a grid trading strategy for
# multiple stocks with different trade
# parameters
# ======================================

import numpy as np

import os
import sys
sys.path.insert(0, os.path.abspath('../'))


if __name__ == '__main__':
    from qteasy.utilfuncs import get_qt_argparser

    import qteasy as qt
    from qteasy import Operator

    class MultiGridTrade(qt.GeneralStg):
        """网格交易策略, 同时监控多只股票并进行网格交易"""

        def realize(self, h, r=None, t=None, pars=None):

            # 此时传入的pars参数为dict对象，dict的key与监控的股票一一对应，value为参数，需分别处理
            pars_dict = self.pars
            if not isinstance(pars_dict, dict):
                raise TypeError(f'self.pars should be a dict, got {type(self.pars)} instead.')
            # 检查参数的个数必须与输入的历史数据价格的层数相同，因为每一层代表一只股票，股票数量必须与参数的数量相同
            if len(pars_dict) != h.shape[0]:
                raise ValueError(
                    f'number of stocks ({h.shape[0]}) does not equal to number of parameters ({len(pars_dict)})')

            trade_signals = np.zeros(shape=(len(pars_dict),))  # 交易信号为一个数组，对应每种股票的交易信号
            for i, symbol, pars in zip(range(len(pars_dict)), pars_dict.keys(), pars_dict.values()):
                # 读取当前保存的策略参数，首次运行时base_grid参数为0，此时买入1000股并设置当前价格为基准网格
                grid_size, trade_batch, base_grid = pars
                # 读取最新价格
                price = h[i, -1, 0]  # 最近一个K线周期的close价格

                # 计算当前价格与当前网格的偏离程度，判断是否产生交易信号
                if base_grid <= 0.01:
                    # 基准网格尚未设置，此时为首次运行，首次买入价值200000元的股票并设置基准网格为当前价格（精确到0.1元）
                    trade_signals[i] = np.round(200000 / price, -2)  # 圆整到100股整数
                    base_grid = np.round(price / 0.1) * 0.1
                elif price - base_grid > grid_size:
                    # 触及卖出网格线，产生卖出信号
                    trade_signals[i] = - trade_batch  # 交易信号等于交易数量，必须使用VS信号类型
                    # 重新计算基准网格
                    base_grid += grid_size
                elif base_grid - price > grid_size:
                    # 触及买入网格线，产生买入信号
                    trade_signals[i] = trade_batch
                    # 重新计算基准网格
                    base_grid -= grid_size
                else:
                    trade_signals[i] = 0.

                # 使用新的基准网格更新交易参数
                if not np.isnan(base_grid):
                    base_grid = np.round(base_grid, 2)
                self.pars[symbol] = (grid_size, trade_batch, base_grid)

            return trade_signals

    parser = get_qt_argparser()
    args = parser.parse_args()
    alpha = MultiGridTrade(
            pars={'000651.SZ': (0.3, 500, 0),
                  '600036.SH': (0.3, 600, 0),
                  '601398.SH': (0.1, 1000, 0)},  # 当基准网格为0时，代表首次运行，此时买入20000股，并设置当前价为基准网格
            par_count=3,
            par_types=['float', 'int', 'float'],
            par_range=[(0.1, 2), (100, 3000), (0, 400)],
            name='MultiGridTrade',
            description='多重网格交易策略，同时监控多只股票，使用不同的策略参数（网格大小和交易批量）执行网格交易',
            strategy_run_timing='close',
            strategy_run_freq='5min',
            data_freq='5min',
            window_length=10,
    )
    datasource = qt.QT_DATA_SOURCE

    if args.restart:
        # clean up all trade data in current account
        from qteasy.trade_recording import delete_account
        delete_account(account_id=args.account, data_source=datasource, keep_account_id=True)

    op = Operator(alpha, signal_type='VS', op_type='step')

    print('in live_grid_multi:', "config['live_trade_daily_refill_tables'] = 'stock_1min...fund_hourly'")
    qt.configure(
            mode=0,
            time_zone='Asia/Shanghai',
            asset_type='E',
            asset_pool=['000651.SZ', '600036.SH', '601398.SH'],
            benchmark_asset='000651.SZ',
            benchmark_asset_type='E',
            benchmark_dtype='close',
            trade_batch_size=100,
            sell_batch_size=1,
            live_trade_account_id=args.account,
            live_trade_account_name=args.new_account,
            live_trade_debug_mode=args.debug,
            live_trade_broker_type='simulator',
            live_trade_ui_type=args.ui,
            watched_price_refresh_interval=5,
            live_trade_daily_refill_tables='stock_1min, stock_5min, stock_15min, stock_30min, stock_hourly, '
                                           'index_1min, index_5min, index_15min, index_30min, index_hourly, '
                                           'fund_1min, fund_5min, fund_15min, fund_30min, fund_hourly',
            live_trade_weekly_refill_tables='stock_daily, index_daily, fund_daily',
            live_trade_data_refill_batch_size=20,
            live_trade_data_refill_batch_interval=3,
    )

    op.run()
