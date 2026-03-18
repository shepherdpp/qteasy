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

from typing import Iterable
from qteasy.strategy import BaseStrategy

from qteasy.blender import (
    blender_parser,
    signal_blend,
    human_blender,
)


class Group:
    """ 策略组，包含多个策略成员，定义了成员策略的信号类型、混合方式、运行频率和时机等属性。 """

    def __init__(self, name: str, signal_type: str = 'pt', blender: str = None,
                 run_freq: str = 'd', run_timing: str = 'close'):
        """ 初始化一个策略组

        Parameters
        ----------
        name: str
            策略组名称，必须为字符串。
        signal_type: str, optional
            策略组信号类型，默认为 'pt'（position），可选
            'ps'（probability）和 'vs'（value）。
        blender: str, optional
            混合器表达式字符串，默认为 None，表示使用默认混合方式
            （'pt' 类型默认乘积，'ps' 和 'vs' 类型默认求和）。如果提供了 blender 字符串，
            将使用 blender_parser 解析该字符串来构建混合器。
        run_freq: str, optional
            运行频率，默认为 'd'（daily）。必须为字符串，且不能为空。
        run_timing: str, optional
            运行时机，默认为 'close'（收盘）。必须为字符串，且不能为空。

        Raises
        ------
        TypeError
            如果 name、signal_type、run_freq 或 run_timing 不是字符串类型。
        ValueError
            如果 signal_type 不是 'pt'、'ps' 或 'vs'，或者 run_freq 或 run_timing 为空。
        """

        if not isinstance(name, str):
            raise TypeError(f'name should be a string, got {type(name)} instead')

        if not isinstance(signal_type, str):
            raise TypeError()

        signal_type = signal_type.lower()
        if signal_type not in ['pt', 'ps', 'vs']:
            raise ValueError()

        # 校验运行频率和运行时机（不能为空，必须为字符串）
        if run_freq is None or run_timing is None:
            raise ValueError('run_freq and run_timing must not be None')
        if not isinstance(run_freq, str):
            raise TypeError(f'run_freq should be a string, got {type(run_freq)} instead')
        if not isinstance(run_timing, str):
            raise TypeError(f'run_timing should be a string, got {type(run_timing)} instead')

        self.name = name
        self._signal_type = signal_type
        self._blender_str = ''
        self._blender = None

        self.members = []
        # 运行时由 Operator 设置，用于在策略中访问 Operator 级别的运行状态（如 process data）
        self._operator = None
        self._run_timing = run_timing
        self._run_freq = run_freq

        if blender:
            self.blender_str = blender

    @property
    def member_strategy_names(self):
        return [strategy.name for strategy in self.members]

    @property
    def member_strategy_ids(self):
        return [strategy.strategy_id for strategy in self.members]

    @property
    def member_strategies(self):
        return self.members

    def _compute_default_blender_str(self) -> str:
        """根据 signal_type 与当前 members 数量实时计算默认 blender 表达式。"""
        n = len(self.members)
        if n == 0:
            return ''
        if self._signal_type in ('ps', 'vs'):
            return '+'.join(f's{i}' for i in range(n))
        return '*'.join(f's{i}' for i in range(n))

    @property
    def blender_str(self):
        if self._blender_str is None or self._blender_str == '':
            return self._compute_default_blender_str()
        return self._blender_str

    @blender_str.setter
    def blender_str(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f'blender_str should be a string, got {type(value)} instead')
        if value:
            try:
                blender_parser(value)
            except Exception as e:
                raise ValueError(
                    f'Invalid blender expression: "{value}" - {e}. '
                    'Default blender will still be used.'
                ) from e
        self._blender_str = value
        self._blender = blender_parser(value) if value else None

    @property
    def blender(self):
        effective = self.blender_str
        if effective:
            return blender_parser(effective)
        return None

    @property
    def human_blender(self):
        strategy_ids = [stg.strategy_id if stg.strategy_id is not None else stg.name for stg in self.members]
        return human_blender(self.blender_str, strategy_ids)

    @property
    def run_freq(self):
        return self._run_freq

    @run_freq.setter
    def run_freq(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f'run_freq should be a string, got {type(value)} instead')
        self._run_freq = value

    @property
    def run_timing(self):
        return self._run_timing

    @run_timing.setter
    def run_timing(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f'run_timing should be a string, got {type(value)} instead')
        self._run_timing = value

    @property
    def signal_type(self):
        return self._signal_type

    @signal_type.setter
    def signal_type(self, value: str):
        if not isinstance(value, str):
            raise TypeError(f'signal_type should be a string, got {type(value)} instead')

        value = value.lower()
        if value not in ['pt', 'ps', 'vs']:
            raise ValueError(f'signal_type should be one of ["pt", "ps", "vs"], got {value} instead')

        self._signal_type = value

    @property
    def strategy_count(self):
        return len(self.members)

    @property
    def group_id(self):
        """Group 的 ID，与 name 相同，用于 Strategy.group_id 兼容"""
        return self.name

    def add_strategy(self, strategy: BaseStrategy) -> None:
        """ 添加一个策略到组中，策略将成为该组的成员。
        
        新增的策略必须是 BaseStrategy 的实例，并且不能已经是该组的成员，否则将引发 ValueError。
        新增策略的 group_id 将被设置为该组的 group_id，以便在策略中访问所属组的信息。

        Parameters
        ----------
        strategy: BaseStrategy
            需要添加到组中的策略实例，必须是 BaseStrategy 的子类实例。

        Returns
        -------
        None

        Raises
        ------
        ValueError
            当 strategy 已经是该组的成员时，抛出 ValueError，提示策略已存在于组中。
        TypeError
            当 strategy 不是 BaseStrategy 的实例时，抛出 TypeError，提示策略类型错误。
        """

        if strategy in self.members:
            raise ValueError(f"Strategy {strategy.name} is already a member of the group {self.name}.")
        self.members.append(strategy)
        strategy._group = self
        strategy._group_id = self.group_id

    def remove_strategy(self, strategy: BaseStrategy):
        """ 从组中移除一个策略，策略将不再是该组的成员。

        被移除的策略必须是该组的成员，否则将引发 ValueError。
        被移除策略的 group_id 将被设置为 None，以表示不再属于任何组。

        Parameters
        ----------
        strategy: BaseStrategy
            需要从组中移除的策略实例，必须是该组的成员。

        Returns
        -------
        None

        Raises
        ------
        ValueError
            当 strategy 不是该组的成员时，抛出 ValueError，提示策略不在组中。
        TypeError
            当 strategy 不是 BaseStrategy 的实例时，抛出 TypeError，提示策略类型错误。
        """
        if strategy in self.members:
            self.members.remove(strategy)
            strategy._group = None
        else:
            raise ValueError(f"Strategy {strategy.name} is not a member of the group {self.name}.")

    def clear_strategies(self):
        """ 清空组中的所有策略，所有成员策略将不再是该组的成员。

        """
        for strategy in self.members:
            strategy._group = None
        self.members = []

    def blend(self, signals: Iterable):
        """使用当前 blender 将同组策略信号混合为一组信号。"""
        return signal_blend(op_signals=signals, blender=self.blender)

    def __repr__(self):
        return f"Group({self.name}, {self.signal_type}, {self.blender_str})"

    def __str__(self):
        return f"{self.name}@{self.run_freq}/{self.run_timing}:{[stg.strategy_id for stg in self.members]}"
