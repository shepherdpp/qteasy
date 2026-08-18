# coding=utf-8
# ======================================
# File:     test_research.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2026-08-15
# Desc:
# Unittest for qteasy.research factor_ic / quantile APIs (M2.2 Phase 8–9).
# ======================================

import unittest

import numpy as np
import pandas as pd

from qteasy.history import HistoryPanel


class TestResearchM22Phase8FactorIc(unittest.TestCase):
    """M2.2 Phase 8：factor_ic / factor_ic_summary。"""

    def _make_panel(self) -> HistoryPanel:
        """3 shares × 2 dates × factor/ret；手算 pearson 金标准。"""
        # date0: factor=[1,2,3], ret=[2,4,6] → perfect positive pearson=1
        # date1: factor=[3,2,1], ret=[1,2,3] → perfect negative pearson=-1
        values = np.array(
            [
                [[1.0, 2.0], [3.0, 1.0]],  # s1
                [[2.0, 4.0], [2.0, 2.0]],  # s2
                [[3.0, 6.0], [1.0, 3.0]],  # s3
            ],
            dtype=float,
        )
        return HistoryPanel(
            values=values,
            levels=['s1', 's2', 's3'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['factor', 'ret'],
        )

    def test_factor_ic_pearson_hand_calc(self):
        """pearson IC 与手算/pandas 金标准一致；index=hdates。"""
        print('\n[TestResearchM22Phase8FactorIc] pearson hand calc')
        from qteasy.research import factor_ic

        hp = self._make_panel()
        ic = factor_ic(hp, 'factor', 'ret', method='pearson')
        print('  ic:\n', ic)
        print('  index:', list(ic.index))
        self.assertIsInstance(ic, pd.Series)
        self.assertEqual(ic.name, 'ic')
        self.assertEqual(len(ic), 2)
        self.assertEqual(list(ic.index), list(hp.hdates))

        f0 = pd.Series([1.0, 2.0, 3.0])
        r0 = pd.Series([2.0, 4.0, 6.0])
        f1 = pd.Series([3.0, 2.0, 1.0])
        r1 = pd.Series([1.0, 2.0, 3.0])
        exp0 = float(f0.corr(r0, method='pearson'))
        exp1 = float(f1.corr(r1, method='pearson'))
        print('  expected:', exp0, exp1)
        self.assertAlmostEqual(float(ic.iloc[0]), exp0)
        self.assertAlmostEqual(float(ic.iloc[1]), exp1)
        self.assertAlmostEqual(float(ic.iloc[0]), 1.0)
        self.assertAlmostEqual(float(ic.iloc[1]), -1.0)

    def test_factor_ic_spearman_and_min_assets(self):
        """默认 spearman；min_assets 不足 → NaN；非法参数。"""
        print('\n[TestResearchM22Phase8FactorIc] spearman and min_assets')
        from qteasy.research import factor_ic

        hp = self._make_panel()
        ic_sp = factor_ic(hp, 'factor', 'ret')  # default spearman
        print('  spearman ic:\n', ic_sp)
        f0 = pd.Series([1.0, 2.0, 3.0])
        r0 = pd.Series([2.0, 4.0, 6.0])
        exp_sp0 = float(f0.corr(r0, method='spearman'))
        print('  expected spearman d0:', exp_sp0)
        self.assertAlmostEqual(float(ic_sp.iloc[0]), exp_sp0)

        # date0: only s1 valid pair if others NaN on factor → 1 asset < min_assets=2
        values = hp.values.copy()
        values[1, 0, 0] = np.nan
        values[2, 0, 0] = np.nan
        hp_nan = HistoryPanel(
            values=values,
            levels=list(hp.shares),
            rows=list(hp.hdates),
            columns=list(hp.htypes),
        )
        ic_min = factor_ic(hp_nan, 'factor', 'ret', method='pearson', min_assets=2)
        print('  ic with min_assets:\n', ic_min)
        self.assertTrue(np.isnan(float(ic_min.iloc[0])))
        self.assertFalse(np.isnan(float(ic_min.iloc[1])))

        with self.assertRaises(ValueError) as cm_m:
            factor_ic(hp, 'factor', 'ret', method='kendall')
        print('  bad method:', cm_m.exception)
        self.assertIn('method', str(cm_m.exception).lower())

        with self.assertRaises(ValueError) as cm_a:
            factor_ic(hp, 'factor', 'ret', min_assets=1)
        print('  bad min_assets:', cm_a.exception)
        self.assertIn('min_assets', str(cm_a.exception).lower())

    def test_factor_ic_unknown_htype_and_empty(self):
        """未知列 ValueError；空面板 → 空 Series。"""
        print('\n[TestResearchM22Phase8FactorIc] unknown htype and empty')
        from qteasy.research import factor_ic

        hp = self._make_panel()
        with self.assertRaises(ValueError) as cm:
            factor_ic(hp, 'nope', 'ret')
        print('  unknown msg:', cm.exception)
        self.assertIn('nope', str(cm.exception))

        empty = factor_ic(HistoryPanel(), 'factor', 'ret')
        print('  empty ic:', empty, 'len:', len(empty))
        self.assertIsInstance(empty, pd.Series)
        self.assertEqual(len(empty), 0)

    def test_factor_ic_summary(self):
        """summary mean/std/ir/win_rate 金标准；空/全 NaN 边界。"""
        print('\n[TestResearchM22Phase8FactorIc] factor_ic_summary')
        from qteasy.research import factor_ic_summary

        ic = pd.Series([1.0, -1.0, 0.5, np.nan], name='ic')
        summary = factor_ic_summary(ic)
        print('  summary:\n', summary)
        valid = ic.dropna()
        exp_mean = float(valid.mean())
        exp_std = float(valid.std(ddof=1))
        exp_ir = exp_mean / exp_std
        exp_wr = float((valid > 0).sum() / len(valid))
        print('  expected mean/std/ir/wr:', exp_mean, exp_std, exp_ir, exp_wr)
        self.assertAlmostEqual(float(summary.loc['mean']), exp_mean)
        self.assertAlmostEqual(float(summary.loc['std']), exp_std)
        self.assertAlmostEqual(float(summary.loc['ir']), exp_ir)
        self.assertAlmostEqual(float(summary.loc['win_rate']), exp_wr)

        all_nan = factor_ic_summary(pd.Series([np.nan, np.nan]))
        print('  all_nan summary:\n', all_nan)
        self.assertTrue(np.isnan(float(all_nan.loc['mean'])))
        self.assertTrue(np.isnan(float(all_nan.loc['ir'])))

        empty_sum = factor_ic_summary(pd.Series(dtype=float))
        print('  empty summary:\n', empty_sum)
        self.assertTrue(np.isnan(float(empty_sum.loc['mean'])))
        self.assertTrue(np.isnan(float(empty_sum.loc['win_rate'])))


class TestResearchM22Phase9Quantile(unittest.TestCase):
    """M2.2 Phase 9：quantile_portfolio / long_short_return。"""

    def _make_panel(self) -> HistoryPanel:
        """4 shares × 2 dates；n_quantiles=2 可手算等权桶收益。"""
        # date0: factor 1,2,3,4 / ret 10,20,30,40
        #   Q1={s1,s2} → 15; Q2={s3,s4} → 35
        # date1: factor 4,3,2,1 / ret 1,2,3,4
        #   Q1={s4,s3} → 3.5; Q2={s2,s1} → 1.5
        values = np.array(
            [
                [[1.0, 10.0], [4.0, 1.0]],  # s1
                [[2.0, 20.0], [3.0, 2.0]],  # s2
                [[3.0, 30.0], [2.0, 3.0]],  # s3
                [[4.0, 40.0], [1.0, 4.0]],  # s4
            ],
            dtype=float,
        )
        return HistoryPanel(
            values=values,
            levels=['s1', 's2', 's3', 's4'],
            rows=['2023-01-01', '2023-01-02'],
            columns=['factor', 'ret'],
        )

    def test_quantile_portfolio_equal_hand_calc(self):
        """等权二分位桶收益与手算金标准一致。"""
        print('\n[TestResearchM22Phase9Quantile] quantile equal hand calc')
        from qteasy.research import quantile_portfolio

        hp = self._make_panel()
        qret = quantile_portfolio(hp, 'factor', 'ret', n_quantiles=2)
        print('  qret:\n', qret)
        self.assertIsInstance(qret, pd.DataFrame)
        self.assertEqual(list(qret.columns), ['Q1', 'Q2'])
        self.assertEqual(list(qret.index), list(hp.hdates))
        self.assertAlmostEqual(float(qret.loc[hp.hdates[0], 'Q1']), 15.0)
        self.assertAlmostEqual(float(qret.loc[hp.hdates[0], 'Q2']), 35.0)
        self.assertAlmostEqual(float(qret.loc[hp.hdates[1], 'Q1']), 3.5)
        self.assertAlmostEqual(float(qret.loc[hp.hdates[1], 'Q2']), 1.5)

    def test_quantile_portfolio_boundaries(self):
        """样本不足 / 非法参数 / 未知列 / 空面板。"""
        print('\n[TestResearchM22Phase9Quantile] quantile boundaries')
        from qteasy.research import quantile_portfolio

        hp = self._make_panel()
        # only 1 valid asset on date0 → < n_quantiles=2 → all NaN that day
        values = hp.values.copy()
        values[1:, 0, :] = np.nan
        hp_few = HistoryPanel(
            values=values,
            levels=list(hp.shares),
            rows=list(hp.hdates),
            columns=list(hp.htypes),
        )
        q_few = quantile_portfolio(hp_few, 'factor', 'ret', n_quantiles=2)
        print('  few assets day0:\n', q_few.iloc[0])
        self.assertTrue(np.isnan(float(q_few.iloc[0]['Q1'])))
        self.assertTrue(np.isnan(float(q_few.iloc[0]['Q2'])))
        # day1 still 4 assets
        print('  day1 Q1/Q2:', q_few.iloc[1]['Q1'], q_few.iloc[1]['Q2'])
        self.assertAlmostEqual(float(q_few.iloc[1]['Q1']), 3.5)
        self.assertAlmostEqual(float(q_few.iloc[1]['Q2']), 1.5)

        with self.assertRaises(ValueError) as cm_n:
            quantile_portfolio(hp, 'factor', 'ret', n_quantiles=1)
        print('  bad n_quantiles:', cm_n.exception)
        self.assertIn('n_quantiles', str(cm_n.exception).lower())

        with self.assertRaises(ValueError) as cm_w:
            quantile_portfolio(hp, 'factor', 'ret', weight='mkt')
        print('  bad weight:', cm_w.exception)
        self.assertIn('weight', str(cm_w.exception).lower())

        with self.assertRaises(ValueError) as cm_h:
            quantile_portfolio(hp, 'nope', 'ret')
        print('  unknown htype:', cm_h.exception)
        self.assertIn('nope', str(cm_h.exception))

        empty = quantile_portfolio(HistoryPanel(), 'factor', 'ret', n_quantiles=3)
        print('  empty shape:', empty.shape, 'cols:', list(empty.columns))
        self.assertEqual(len(empty), 0)
        self.assertEqual(list(empty.columns), ['Q1', 'Q2', 'Q3'])

    def test_long_short_return(self):
        """long - short 金标准；缺列 ValueError。"""
        print('\n[TestResearchM22Phase9Quantile] long_short_return')
        from qteasy.research import long_short_return, quantile_portfolio

        hp = self._make_panel()
        qret = quantile_portfolio(hp, 'factor', 'ret', n_quantiles=2)
        ls = long_short_return(qret, long='Q2', short='Q1')
        print('  long_short:\n', ls)
        self.assertEqual(ls.name, 'long_short')
        self.assertAlmostEqual(float(ls.iloc[0]), 35.0 - 15.0)
        self.assertAlmostEqual(float(ls.iloc[1]), 1.5 - 3.5)

        # default long=Q5 short=Q1 on fabricated frame
        fake = pd.DataFrame(
            {'Q1': [1.0, 2.0], 'Q5': [3.0, 4.0]},
            index=pd.to_datetime(['2023-01-01', '2023-01-02']),
        )
        ls_def = long_short_return(fake)
        print('  default Q5-Q1:\n', ls_def)
        self.assertAlmostEqual(float(ls_def.iloc[0]), 2.0)
        self.assertAlmostEqual(float(ls_def.iloc[1]), 2.0)

        with self.assertRaises(ValueError) as cm:
            long_short_return(qret, long='Q9', short='Q1')
        print('  missing col:', cm.exception)
        self.assertTrue(len(str(cm.exception)) > 0)


if __name__ == '__main__':
    unittest.main()
