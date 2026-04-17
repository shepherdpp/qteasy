# coding=utf-8
# ======================================
# File: registry.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳技能注册中心，负责
# 注册、发现与调用技能实现。
# ======================================

"""Skill 注册与发现。

SkillRegistry 在阶段A中承担最小“插件容器”职责：
- 注册：把技能元数据和实现函数绑定；
- 发现：支持列出技能和读取元数据；
- 调用：按名称分发到具体 handler。

后续阶段可在该容器基础上扩展版本协商、命名空间隔离、权限检查等能力。
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from .contracts import SkillMetadata
from .runtime import SkillRuntime


class SkillRegistry:
    """管理技能注册、查询与调用。"""

    def __init__(self, runtime: Optional[SkillRuntime] = None) -> None:
        # 元数据与实现分离存储，便于：
        # 1) Planner 仅读 metadata 不触发执行；
        # 2) Executor 仅按名称分发调用 handler。
        self._meta: Dict[str, SkillMetadata] = {}
        self._impl: Dict[str, Callable[..., dict]] = {}
        self._runtime = runtime or SkillRuntime()

    def register(self, metadata: SkillMetadata, handler: Callable[..., dict]) -> None:
        """注册技能。

        Parameters
        ----------
        metadata : SkillMetadata
            技能说明信息。
        handler : Callable[..., dict]
            技能执行函数，要求返回结构化字典。
        """

        if metadata.name in self._meta:
            raise ValueError(f'Skill "{metadata.name}" already registered.')
        self._meta[metadata.name] = metadata
        self._impl[metadata.name] = handler

    def get_metadata(self, skill_name: str) -> SkillMetadata:
        """返回技能元数据。

        规划阶段会调用该方法获取 side_effects 等信息，用于构造可审阅计划。
        """

        if skill_name not in self._meta:
            raise KeyError(f'Skill "{skill_name}" is not registered.')
        return self._meta[skill_name]

    def list_skills(self) -> List[SkillMetadata]:
        """返回已注册技能列表。

        返回按技能名排序后的稳定顺序，便于测试断言和前端展示。
        """

        return [self._meta[name] for name in sorted(self._meta)]

    def call(self, skill_name: str, *, confirmed: bool = True, **kwargs) -> dict:
        """调用技能实现。

        Parameters
        ----------
        skill_name : str
            技能名称。
        **kwargs
            技能入参。

        Returns
        -------
        dict
            技能返回的结构化结果。
        """

        if skill_name not in self._impl:
            raise KeyError(f'Skill "{skill_name}" is not registered.')
        return self._runtime.execute(
            metadata=self._meta[skill_name],
            handler=self._impl[skill_name],
            kwargs=kwargs,
            confirmed=confirmed,
        )
