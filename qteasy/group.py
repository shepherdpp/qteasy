# coding=utf-8
# ======================================
# File:     group.py
# Author:   Jackie PENG
# Contact:  jackie.pengzhao@gmail.com
# Created:  2025-07-29
# Desc:
#   Definition of Group class, a
# collection of strategies in the
# Operator class, managing blender of
# strategy running results. All
# strategies in the same group runs
# together.
# ======================================

import numpy as np
from qteasy.strategy import BaseStrategy

from qteasy.blender import (
    blender_parser,
    signal_blend,
    human_blender,
)


class Group:
    def __init__(self, name: str, signal_type: str = 'PT', blender: str = None):

        self.name = name
        self.signal_type = signal_type
        self.blender_str = blender
        self._blender = blender_parser(blender)

        self.members = []
        self.run_timing = None
        self.run_freq = None

    @property
    def member_strategies(self):
        return [strategy.name for strategy in self.members]

    @property
    def blender(self):
        return human_blender(self.blender_str, self.members)

    def add_strategy(self, strategy: BaseStrategy):

        if len(self.members) == 0:
            self.members.append(strategy)
            self.run_freq = strategy.run_freq
            self.run_timing = strategy.run_timing
        else:
            if strategy in self.members:
                raise ValueError(f"Strategy {strategy.name} is already a member of the group {self.name}.")
            if strategy.run_timing != self.run_timing:
                raise ValueError(f"Strategy {strategy.name} has a different run timing than the group {self.name}.")
            if strategy.run_freq != self.run_freq:
                raise ValueError(f"Strategy {strategy.name} has a different run frequency than the group {self.name}.")
            self.members.append(strategy)

    def blend(self, signals: np.ndarray):
        """Set the blender for the group."""
        return signal_blend(op_signals=signals, blender=self._blender)

    def human_blender(self):
        return human_blender(self.blender_str, self.members)

    def __repr__(self):
        return f"Group(name={self.name}, members={self.members})"