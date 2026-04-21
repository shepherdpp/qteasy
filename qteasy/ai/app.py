# coding=utf-8
# ======================================
# File: app.py
# Author: Jackie PENG
# Contact: jackie.pengzhao@gmail.com
# Created: 2026-04-15
# Desc:
# qteasy AI 外壳应用层入口，统一编排
# Notebook / CLI 调用链路。
# ======================================

"""阶段A统一入口（Notebook/CLI 共用）。

这个模块定位为“装配层（assembly layer）”，负责把分散模块按固定拓扑连接：

1. `SkillRegistry`：技能注册中心；
2. `Planner`：自然语言到 ToolPlan；
3. `PlanExecutor`：计划执行与 run 落盘；
4. `MemoryStore`：profile/env_facts/runs 存储。

设计目标
--------
- 对 Notebook 用户暴露简单 API（ask/plan/run）；
- 对 CLI 和未来 Web/TUI 保持一致的应用层语义；
- 避免前端直接感知技能细节与执行细节。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .config import ConfigCenter
from .executor import PlanExecutor
from .memory_store import MemoryStore
from .planner import Planner
from .provider import BaseLLMProvider
from .registry import SkillRegistry
from .skills import (
    build_data_summary_skill,
    build_strategy_meta_get_skill,
    build_strategy_meta_list_skill,
    build_system_fallback_skill,
    build_visual_export_skill,
)


def build_default_registry() -> SkillRegistry:
    """构建阶段A默认 Registry。

    Returns
    -------
    SkillRegistry
        已注册阶段A默认只读技能的注册中心实例。

    Notes
    -----
    这里按固定顺序注册技能，便于：
    - 测试时得到稳定输出；
    - 阅读时清楚看到阶段A能力边界。
    """

    registry = SkillRegistry()
    for builder in [
        build_strategy_meta_list_skill,
        build_strategy_meta_get_skill,
        build_data_summary_skill,
        build_visual_export_skill,
        build_system_fallback_skill,
    ]:
        metadata, handler = builder()
        registry.register(metadata, handler)
    return registry


@dataclass
class AssistantResponse:
    """统一返回对象（预留类型）。

    Notes
    -----
    当前阶段A主要以 `dict` 返回，保留该 dataclass 是为了后续在
    类型系统中逐步收敛响应对象结构。
    """

    plan: Dict[str, Any]
    execution: Dict[str, Any]
    run_id: str
    run_file: str


class QteasyAssistant:
    """Notebook/CLI 共用助手对象。

    这是用户最直接接触的 AI 外壳对象，面向“用户意图”而不是“内部模块”。
    用户只需要选择调用模式：

    - `ask()`：只问不执行；
    - `plan()`：生成 dry-run 计划；
    - `run()`：确认执行计划。
    """

    def __init__(
        self,
        *,
        provider: Optional[BaseLLMProvider] = None,
        memory_store: Optional[MemoryStore] = None,
        registry: Optional[SkillRegistry] = None,
    ) -> None:
        # MemoryStore：负责持久化执行记录与轻量记忆。
        self.memory_store = memory_store or MemoryStore()
        # Registry：聚合本阶段可用技能及其元数据。
        self.registry = registry or build_default_registry()
        # Planner：根据用户请求生成计划对象。
        self.planner = Planner(self.registry, provider=provider)
        # Executor：负责按计划执行并落盘 run 记录。
        self.executor = PlanExecutor(self.registry, self.memory_store)

    def ask(self, query: str) -> Dict[str, Any]:
        """Ask 模式：仅返回 plan，不执行技能。

        Parameters
        ----------
        query : str
            用户自然语言请求。

        Returns
        -------
        Dict[str, Any]
            dry-run 执行结果（无技能调用），用于解释和预览。
        """

        plan = self.planner.build_plan(query, mode="ask")
        payload = self.executor.execute(plan, confirm=False)
        return payload

    def plan(self, query: str) -> Dict[str, Any]:
        """Plan 模式：生成 dry_run 计划。

        与 `ask()` 的区别在于：
        - ask：通常无步骤，强调“问答解释”；
        - plan：通常会生成可执行步骤，强调“执行前审阅”。
        """

        plan = self.planner.build_plan(query, mode="plan")
        payload = self.executor.execute(plan, confirm=False)
        return payload

    def run(self, query: str) -> Dict[str, Any]:
        """Plan + 确认执行。

        工作流程：
        1) 先由 Planner 生成 ToolPlan；
        2) 将 execution_mode 切换为 execute；
        3) 交给 Executor 实际执行并写入 runs。
        """

        plan = self.planner.build_plan(query, mode="plan")
        plan.execution_mode = "execute"
        payload = self.executor.execute(plan, confirm=True)
        return payload

    def debug_config(self) -> Dict[str, Any]:
        """返回当前 AI 配置诊断信息（不泄露密钥）。"""

        config_center = ConfigCenter()
        provider_cfg = config_center.resolve_provider_config()
        trace = config_center.get_trace()
        api_key = str(provider_cfg.get("api_key", "")).strip()
        return {
            "provider_enabled": self.planner.provider is not None,
            "model": str(provider_cfg.get("model", "")).strip(),
            "base_url": str(provider_cfg.get("base_url", "")).strip(),
            "timeout": int(provider_cfg.get("timeout", 30)),
            "api_key_present": bool(api_key),
            "config_sources": {key: item.get("source", "") for key, item in trace.items()},
        }
