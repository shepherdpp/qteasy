# coding=utf-8
# build_in.py

# ======================================
# This file contains concrete strategy
# classes that are inherited form
# strategy.Strategy class and its sub
# classes like strategy.RollingTiming
# etc.
# ======================================

import qteasy.strategy as stg


class TestTimingClass(stg.RollingTiming):
    """Test strategy that uses abstract class from another file
    """
    def __init__(self):
        """

        """
        super().__init__()
        pass

    def _realize(self, hist_data, params):
        print(f'test strategy with imported abc done!\n'
              f'got parameters: {params}\n'
              f'got hist data shaped: {hist_data.shape}')