# coding=utf-8
# ======================================
# File: __init__.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳包导出入口，汇总
# 阶段A公开类型与核心对象。
# ======================================

"""qteasy AI 外壳模块（S1.4 阶段A）。"""

from .contracts import (
    PlanExecutionRecord,
    PlanStepRecord,
    SkillError,
    SkillMetadata,
    SkillResult,
    SkillSideEffects,
    ToolPlan,
    ToolStep,
    new_plan_id,
    new_run_id,
)
from .executor import PlanExecutor
from .config import ConfigCenter
from .memory_store import MemoryStore
from .planner import Planner
from .provider import BaseLLMProvider, OpenAICompatProvider
from .registry import SkillRegistry
from .runtime import SkillRuntime

__all__ = [
    "SkillMetadata",
    "SkillSideEffects",
    "ToolStep",
    "ToolPlan",
    "SkillError",
    "SkillResult",
    "PlanStepRecord",
    "PlanExecutionRecord",
    "new_plan_id",
    "new_run_id",
    "SkillRegistry",
    "Planner",
    "PlanExecutor",
    "ConfigCenter",
    "SkillRuntime",
    "MemoryStore",
    "BaseLLMProvider",
    "OpenAICompatProvider",
]
