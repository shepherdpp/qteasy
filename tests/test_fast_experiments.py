# coding=utf-8
# ======================================
# File:     test_fast_experiments.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2020-02-12
# Desc:
#   Temporary test file for quick
#   function tests.
# ======================================
import unittest

import qteasy as qt
import numpy as np


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


class FastExperiments(unittest.TestCase):
    """This test case is created to have experiments done that can be quickly called from Command line"""

    def setUp(self):
        pass

    def test_fast_experiments(self):
        """temp test"""
        # op = qt.Operator(strategies='dma')
        # op.set_parameter('dma', pars=(23, 166, 196))
        # res = qt.run(op, mode=1, invest_start='20160501', visual=True, trade_log=True)
        self.assertEqual(1, 1)

        shares = qt.filter_stock_codes(index='000300.SH', date='20190501')
        print(len(shares), shares[:10])
        alpha = MultiFactors()
        op = qt.Operator(alpha, signal_type='PT')
        op.op_type = 'stepwise'
        op.set_blender('close', "0.8*s0")
        op.run(mode=1,
               invest_start='20190501',
               invest_end='20220501',
               asset_type='E',
               asset_pool=shares,
               trade_batch_size=100,
               sell_batch_size=1,
               trade_log=True)


if __name__ == '__main__':
    unittest.main()