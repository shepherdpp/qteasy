Optimizer 策略优化器
===================================

Optimizer 是一个策略优化器，可以通过遗传算法、粒子群算法等方法来优化策略参数。

.. autoclass:: qteasy.optimization.Optimizer

策略参数优化方法
===============================

网格搜索
---------------------------

.. autoclass:: qteasy.optimization.Optimizer._search_grid

蒙特卡洛搜索
---------------------------

.. autoclass:: qteasy.optimization.Optimizer._search_montecarlo

模拟退火搜索
---------------------------

.. autoclass:: qteasy.optimization.Optimizer._search_sa

遗传算法搜索
---------------------------

.. autoclass:: qteasy.optimization.Optimizer._search_ga

梯度下降搜索
---------------------------

.. autoclass:: qteasy.optimization.Optimizer._search_gradient

粒子群算法搜索
---------------------------

.. autoclass:: qteasy.optimization.Optimizer._search_pso

贝叶斯优化搜索
---------------------------

.. autoclass:: qteasy.optimization.Optimizer._search_bayesian