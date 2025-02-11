# coding=utf-8
# ======================================
# File:     test_user_defined.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Test file for user-defined
# strategies.
# ======================================
import unittest

import qteasy as qt
import numpy as np

from qteasy import QT_CONFIG


def market_value_weighted(stock_return, mv, mv_cat, bp_cat, mv_target, bp_target):
    """ 根据mv_target和bp_target计算市值加权收益率

    """
    sel = (mv_cat == mv_target) & (bp_cat == bp_target)
    mv_total = np.nansum(mv[sel])
    mv_weight = mv / mv_total
    return_total = np.nansum(stock_return[sel] * mv_weight[sel])
    return return_total


class MultiFactors(qt.FactorSorter):

    def __init__(self, pars: tuple = (0.5, 0.3, 0.7)):
        super().__init__(
                pars=pars,
                par_count=3,
                par_types=['float', 'float', 'float'],  # 参数1:大小市值分类界限，参数2:小/中bp分界线，参数3，中/大bp分界线
                par_range=[(0.01, 0.99), (0.01, 0.49), (0.50, 0.99)],
                name='MultiFactor',
                description='根据Fama-French三因子回归模型估算HS300成分股的alpha值选股',
                strategy_run_timing='close',  # 在周期结束（收盘）时运行
                strategy_run_freq='m',  # 每月执行一次选股（每周或每天都可以）
                strategy_data_types='pb, total_mv, close',  # 执行选股需要用到的股票数据
                data_freq='d',  # 数据频率（包括股票数据和参考数据）
                window_length=20,
                use_latest_data_cycle=True,
                reference_data_types='close-000300.SH',  # 选股需要用到市场收益率，作为参考数据传入
                max_sel_count=10,  # 最多选出10支股票
                sort_ascending=True,  # 选择因子最小的股票
                condition='less',  # 仅选择因子小于某个值的股票
                lbound=0,  # 仅选择因子小于0的股票
                ubound=0,  # 仅选择因子小于0的股票
        )

    def realize(self, h, r=None, t=None, pars=None):

        size_gate_percentile, bp_small_percentile, bp_large_percentile = self.pars
        # 读取投资组合的数据PB和total_MV的最新值
        pb = h[:, -1, 0]  # 当前所有股票的PB值
        mv = h[:, -1, 1]  # 当前所有股票的市值
        pre_close = h[:, -2, 2]  # 当前所有股票的前收盘价
        close = h[:, -1, 2]  # 当前所有股票的最新收盘价

        # 读取参考数据(r)
        market_pre_close = r[-2, 0]  # HS300的昨收价
        market_close = r[-1, 0]  # HS300的收盘价

        # 计算账面市值比，为pb的倒数
        bp = pb ** -1
        # 计算市值的50%的分位点,用于后面的分类
        size_gate = np.nanquantile(mv, size_gate_percentile)
        # 计算账面市值比的30%和70%分位点,用于后面的分类
        bm_30_gate = np.nanquantile(bp, bp_small_percentile)
        bm_70_gate = np.nanquantile(bp, bp_large_percentile)
        # 计算每只股票的当日收益率
        stock_return = pre_close / close - 1

        # 根据每只股票的账面市值比和市值，给它们分配bp分类和mv分类
        # 市值小于size_gate的cat为1，否则为2
        mv_cat = np.ones_like(mv)
        mv_cat += (mv > size_gate).astype('float')
        # bp小于30%的cat为1，30%～70%之间为2，大于70%为3
        bp_cat = np.ones_like(bp)
        bp_cat += (bp > bm_30_gate).astype('float')
        bp_cat += (bp > bm_70_gate).astype('float')

        # 获取小市值组合的市值加权组合收益率
        smb_s = (market_value_weighted(stock_return, mv, mv_cat, bp_cat, 1, 1) +
                 market_value_weighted(stock_return, mv, mv_cat, bp_cat, 1, 2) +
                 market_value_weighted(stock_return, mv, mv_cat, bp_cat, 1, 3)) / 3
        # 获取大市值组合的市值加权组合收益率
        smb_b = (market_value_weighted(stock_return, mv, mv_cat, bp_cat, 2, 1) +
                 market_value_weighted(stock_return, mv, mv_cat, bp_cat, 2, 2) +
                 market_value_weighted(stock_return, mv, mv_cat, bp_cat, 2, 3)) / 3
        smb = smb_s - smb_b
        # 获取大账面市值比组合的市值加权组合收益率
        hml_b = (market_value_weighted(stock_return, mv, mv_cat, bp_cat, 1, 3) +
                 market_value_weighted(stock_return, mv, mv_cat, bp_cat, 2, 3)) / 2
        # 获取小账面市值比组合的市值加权组合收益率
        hml_s = (market_value_weighted(stock_return, mv, mv_cat, bp_cat, 1, 1) +
                 market_value_weighted(stock_return, mv, mv_cat, bp_cat, 2, 1)) / 2
        hml = hml_b - hml_s

        # 计算市场收益率
        market_return = market_pre_close / market_close - 1

        coff_pool = []
        # 对每只股票进行回归获取其alpha值
        for rtn in stock_return:
            x = np.array([[market_return, smb, hml, 1.0]])
            y = np.array([[rtn]])
            # OLS估计系数
            coff = np.linalg.lstsq(x, y)[0][3][0]
            coff_pool.append(coff)

        # 以alpha值为股票组合的选股因子执行选股
        factors = np.array(coff_pool)

        return factors


class IndexEnhancement(qt.GeneralStg):

    def __init__(self, pars: tuple = (0.35, 0.8, 5)):
        super().__init__(
                pars=pars,
                par_count=2,
                par_types=['float', 'float', 'int'],  # 参数1:沪深300指数权重阈值，低于它的股票不被选中，参数2: 初始权重，参数3: 连续涨跌天数，作为强弱势判断阈值
                par_range=[(0.01, 0.99), (0.51, 0.99), (2, 20)],
                name='IndexEnhancement',
                description='跟踪HS300指数选股，并根据连续上涨/下跌趋势判断强弱势以增强权重',
                strategy_run_timing='close',  # 在周期结束（收盘）时运行
                strategy_run_freq='d',  # 每天执行一次选股
                strategy_data_types='wt-000300.SH, close',  # 利用HS300权重设定选股权重, 根据收盘价判断强弱势
                data_freq='d',  # 数据频率（包括股票数据和参考数据）
                window_length=20,
                use_latest_data_cycle=True,
                reference_data_types='',  # 不需要使用参考数据
        )

    def realize(self, h, r=None, t=None, pars=None):
        weight_threshold, init_weight, price_days = self.pars
        # 读取投资组合的权重wt和最近price_days天的收盘价
        wt = h[:, -1, 0]  # 当前所有股票的权重值
        pre_close = h[:, -price_days - 1:-1, 1]
        close = h[:, -price_days:, 1]  # 当前所有股票的最新连续收盘价
        # 计算连续price_days天的收益
        stock_returns = pre_close - close  # 连续p天的收益

        # 设置初始选股权重为0.8
        weights = init_weight * np.ones_like(wt)

        # 剔除掉权重小于weight_threshold的股票
        weights[wt < weight_threshold] = 0

        # 找出强势股，将其权重设为1, 找出弱势股，将其权重设置为 init_weight - (1 - init_weight)
        up_trends = np.all(stock_returns > 0, axis=1)
        weights[up_trends] = 1.0
        down_trend_weight = init_weight - (1 - init_weight)
        down_trends = np.all(stock_returns < 0, axis=1)
        weights[down_trends] = down_trend_weight

        # 实际选股权重为weights * HS300权重
        weights *= wt
        # print(f'select weight is: \n{weights}')

        return weights


class GridTrading(qt.GeneralStg):

    def __init__(self, pars: tuple = (2.0, 3.0, 0.3, 0.5, 300)):
        super().__init__(
                pars=pars,
                par_count=5,
                par_types=['float', 'float', 'float', 'float', 'int'],
                # 仓位配置的阈值：参数1:低仓位阈值，参数2: 高仓位阈值，参数3：低仓位比例，参数4:高仓位比例，参数5:计算天数
                par_range=[(0.5, 3.0), (2.0, 10.), (0.01, 0.5), (0.5, 0.99), (10, 300)],
                name='GridTrading',
                description='根据过去300份钟的股价均值和标准差，改变投资金额的仓位',
                strategy_run_timing='close',  # 在周期结束（收盘）时运行
                strategy_run_freq='1min',  # 每份钟执行一次调整
                strategy_data_types='close',  # 使用份钟收盘价调整
                data_freq='1min',  # 数据频率（包括股票数据和参考数据）
                window_length=300,
                use_latest_data_cycle=False,  # 高频数据不需要使用当前数据区间
                reference_data_types='',  # 不需要使用参考数据
        )

    def realize(self, h, r=None, t=None, pars=None):
        """策略输出PT信号，即仓位目标信号"""

        low_threshold, high_threshold, low_pos, hi_pos, days = self.pars

        # 读取最近N天的收盘价
        close = h[:, - days:, 0]  # 最新连续收盘价
        current_close = h[:, -1, 0]  # 当天的收盘价

        # 计算N天的平均价和标准差，并计算仓位阈值
        close_mean = np.nanmean(close, axis=1)
        close_std = np.nanstd(close, axis=1)
        hi_positive = close_mean + high_threshold * close_std
        low_positive = close_mean + low_threshold * close_std
        low_negative = close_mean - low_threshold * close_std
        hi_negative = close_mean - high_threshold * close_std

        # 根据当前的实际价格确定目标仓位，并将目标仓位作为信号输出
        pos = np.zeros_like(close_mean)
        pos = np.where(current_close > hi_positive, hi_pos, pos)
        pos = np.where(hi_positive >= current_close > low_positive, low_pos, pos)
        pos = np.where(low_positive >= current_close > low_negative, 0, pos)
        pos = np.where(low_negative >= current_close > hi_negative, - low_pos, pos)
        pos = np.where(current_close >= hi_negative, - hi_pos, pos)

        return pos


class FastExperiments(unittest.TestCase):
    """This test case is created to have experiments done that can be quickly called from Command line"""

    def setUp(self):
        from qteasy import DataSource, QT_CONFIG
        self.test_ds = DataSource(
                source_type='db',
                host=QT_CONFIG['test_db_host'],
                port=QT_CONFIG['test_db_port'],
                user=QT_CONFIG['test_db_user'],
                password=QT_CONFIG['test_db_password'],
                db_name=QT_CONFIG['test_db_name']
        )

    def test_multi_factors(self):
        """ test strategy MultiFactors"""
        self.assertEqual(1, 1)
        shares = qt.filter_stock_codes(index='000300.SH', date='20210101')
        print(len(shares), shares[:10])

        alpha = MultiFactors()
        op = qt.Operator(alpha, signal_type='PT')

        op.op_type = 'stepwise'
        op.set_blender("0.8*s0", 'close')
        # op.run(mode=1,
        #        invest_start='20210101',
        #        invest_end='20220501',
        #        asset_type='E',
        #        invest_cash_amounts=[1000000],
        #        asset_pool=shares,
        #        trade_batch_size=100,
        #        sell_batch_size=1,
        #        trade_log=True)
        self.assertTrue(True)

    def test_index_enhancement(self):
        """ tests for self-defined strategies"""
        self.assertEqual(1, 1)

        shares = qt.filter_stock_codes(index='000300.SH', date='20210101')
        print(len(shares), shares[:10])

        alpha = IndexEnhancement()
        op = qt.Operator(alpha, signal_type='PT')

        op.op_type = 'stepwise'
        op.set_blender("0.8*s0", 'close')
        # op.run(mode=1,
        #        invest_start='20210101',
        #        invest_end='20220501',
        #        asset_type='E',
        #        invest_cash_amounts=[1000000],
        #        asset_pool=shares,
        #        trade_batch_size=100,
        #        sell_batch_size=1,
        #        trade_log=True)
        self.assertTrue(True)

    def test_grid_trading(self):
        """ test for strategy GridTrading"""
        self.assertEqual(1, 1)

        alpha = GridTrading()
        op = qt.Operator(alpha, signal_type='PT')

        op.op_type = 'batch'
        op.set_blender("1.0*s0", 'close')
        # op.run(
        #         mode=1,
        #         invest_start='20220401',
        #         invest_end='20220731',
        #         invest_cash_amounts=[1000000],
        #         asset_type='IDX',
        #         asset_pool=['000300.SH'],
        #         trade_batch_size=0,
        #         sell_batch_size=0,
        #         trade_log=True,
        #         allow_sell_short=True,
        # )
        self.assertTrue(True)

    def test_get_history_data(self):
        """
        """
        # extract normal data
        data = qt.get_history_data(htypes='open, high, low, close',
                                   start='20211230',
                                   end='20220110',
                                   shares='000001.SZ',
                                   freq='d',
                                   adj='n',
                                   asset_type='E')
        print(f'not adjusted data: \n{data}')
        # extract back adjusted price for one asset
        data = qt.get_history_data(htypes='open, high, low, close',
                                   start='20211230',
                                   end='20220110',
                                   shares='000001.SZ',
                                   freq='d',
                                   adj='b',
                                   asset_type='E')
        print(f'adjusted data: \n{data}')
        # extract back adjusted prices for both assets mixed
        data = qt.get_history_data(htypes='open, high, low, close',
                                   start='20211230',
                                   end='20220110',
                                   shares='000001.SZ, 512000.SH',
                                   freq='d',
                                   adj='b',
                                   asset_type='E, FD')
        print(f'adjusted data: \n{data}')
        self.assertTrue(True)

    def test_fetch_and_save(self):
        """ test fetch and save data"""
        from qteasy.data_channels import fetch_real_time_klines
        from qteasy.datatables import set_primary_key_frame, set_primary_key_index

        data = fetch_real_time_klines(freq='15min', channel='eastmoney', qt_codes='000651.SZ')
        print(data)
        df = data.copy()
        df = set_primary_key_frame(df, ['trade_time'], ['datetime'])
        set_primary_key_index(df, ['trade_time'], ['datetime'])
        self.test_ds.update_table_data('stock_5min', df=data, merge_type='update')


if __name__ == '__main__':
    unittest.main()