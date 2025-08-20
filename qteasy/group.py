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
from typing import Iterable
from qteasy.strategy import BaseStrategy

from qteasy.blender import (
    blender_parser,
    signal_blend,
    human_blender,
)


class Group:
    def __init__(self, name: str, signal_type: str = 'PT', blender: str = None):

        if not isinstance(name, str):
            raise TypeError(f'name should be a string, got {type(name)} instead')

        if not isinstance(signal_type, str):
            raise TypeError()

        signal_type = signal_type.upper()
        if signal_type not in ['PT', 'PS', 'VS']:
            raise ValueError()

        self.name = name
        self._signal_type = signal_type
        self._blender_str = ''
        self._blender = None

        self.members = []
        self._run_timing = None
        self._run_freq = None

        if blender:
            self.blender_str = blender

    @property
    def member_strategies(self):
        return [strategy.name for strategy in self.members]

    @property
    def blender_str(self):
        return self._blender_str

    @blender_str.setter
    def blender_str(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f'blender_str should be a string, got {type(value)} instead')
        self._blender_str = value
        self._blender = blender_parser(value) if value else None

    @property
    def blender(self):
        return self._blender

    @property
    def human_blender(self):
        strategy_ids = [stg.name for stg in self.members]
        return human_blender(self.blender_str, strategy_ids)

    @property
    def run_freq(self):
        return self._run_freq

    @property
    def run_timing(self):
        return self._run_timing

    @property
    def signal_type(self):
        return self._signal_type

    @property
    def strategy_count(self):
        return len(self.members)

    def add_strategy(self, strategy: BaseStrategy):

        if len(self.members) == 0:
            self.members.append(strategy)
            self._run_freq = strategy.run_freq
            self._run_timing = strategy.run_timing
        else:
            if strategy in self.members:
                raise ValueError(f"Strategy {strategy.name} is already a member of the group {self.name}.")
            if strategy.run_timing != self.run_timing:
                raise ValueError(f"Run timing of Strategy {strategy.name} ({strategy.run_timing}) "
                                 f"if different from the group {self.name}.")
            if strategy.run_freq != self.run_freq:
                raise ValueError(f"Strategy {strategy.name} has a different run frequency than the group {self.name}.")
            self.members.append(strategy)

    def blend(self, signals: Iterable):
        """Set the blender for the group."""
        return signal_blend(op_signals=signals, blender=self._blender)

    def __repr__(self):
        return f"{self.name}({self.signal_type}) with {self.strategy_count} stgs"

    def __str__(self):
        return f"{self.name}({self.strategy_count}IN{self.signal_type})@{self.run_freq}/{self.run_timing}"